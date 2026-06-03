# llm.py
import json
from openai import OpenAI
from config import OPENAI_API_KEY
from logger import get_logger

log = get_logger("llm")
client = OpenAI(api_key=OPENAI_API_KEY)

SUMMARY_SYSTEM_PROMPT = """
You are a contact center AI assistant specialising in call analysis.

When given a call transcript, you produce a structured call summary.

Your summary must always include:
- issue: the customer's primary problem in one sentence
- resolution: what the agent did to resolve it
- sentiment: customer sentiment — positive, neutral, or negative
- next_best_action: one concrete action the agent should take after the call

Be concise. No filler phrases. No "certainly" or "of course".
You must respond with ONLY a raw JSON object. No markdown. No code fences. No backticks. No explanation. The first character of your response must be { and the last must be }.
"""

SUMMARY_SCHEMA = {
    "name": "generate_call_summary",
    "description": "Generate a structured summary from a call transcript",
    "parameters": {
        "type": "object",
        "properties": {
            "issue": {
                "type": "string",
                "description": "The customer's primary problem in one sentence"
            },
            "resolution": {
                "type": "string",
                "description": "What the agent did to resolve the issue"
            },
            "sentiment": {
                "type": "string",
                "enum": ["positive", "neutral", "negative"],
                "description": "Overall customer sentiment during the call"
            },
            "next_best_action": {
                "type": "string",
                "description": "One concrete action the agent should take after the call"
            },
            "escalation_required": {
                "type": "boolean",
                "description": "Whether this call needs supervisor escalation"
            }
        },
        "required": ["issue", "resolution", "sentiment", "next_best_action", "escalation_required"]
    }
}


async def generate_call_summary(transcript: str) -> dict:
    log.info(f"generate_call_summary | transcript_len={len(transcript)} | calling LLM")

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        max_tokens=500,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user",   "content": f"Transcript:\n{transcript}"}
        ]
    )

    raw = response.choices[0].message.content
    log.info(f"generate_call_summary | tokens_used={response.usage.total_tokens} | raw_len={len(raw)}")

    try:
        clean = raw.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1])
        summary = json.loads(clean)
        log.info(f"generate_call_summary | parsed | issue={summary.get('issue', '')[:50]}")
        return summary
    except json.JSONDecodeError:
        log.error(f"generate_call_summary | JSON parse failed | raw={raw[:200]}")
        raise ValueError(f"LLM returned non-JSON: {raw[:200]}")


async def generate_call_summary_structured(transcript: str) -> dict:
    log.info(f"generate_call_summary_structured | transcript_len={len(transcript)} | calling LLM")

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        max_tokens=500,
        messages=[
            {
                "role": "system",
                "content": "You are a contact center AI assistant. Analyse the transcript and call the generate_call_summary function."
            },
            {
                "role": "user",
                "content": f"Transcript:\n{transcript}"
            }
        ],
        tools=[{"type": "function", "function": SUMMARY_SCHEMA}],
        tool_choice={"type": "function", "function": {"name": "generate_call_summary"}}
    )

    tool_call = response.choices[0].message.tool_calls[0]
    summary = json.loads(tool_call.function.arguments)

    log.info(f"generate_call_summary_structured | tokens_used={response.usage.total_tokens} | sentiment={summary['sentiment']} | escalation={summary['escalation_required']}")
    return summary

COT_SYSTEM_PROMPT = """
You are a senior contact center AI analyst with 10 years of experience.

When analysing a call transcript, you reason step by step before producing your output.

Your reasoning process:
1. EMOTIONAL ARC: How did the customer's sentiment change from start to end?
2. RESOLUTION STATUS: Was the issue fully resolved, partially resolved, or unresolved?
3. RETENTION RISK: Is there any risk the customer might churn or escalate further?
4. AGENT PERFORMANCE: Did the agent handle this well? Any missed opportunities?
5. NEXT BEST ACTION: Given the above, what is the single most important action?

After reasoning through these five points, produce your structured output.
You must call the generate_call_summary function with your final answer.
Do not include your reasoning in the function output — only the conclusions.
"""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """Transcript:
Agent: Hi, billing support, how can I help?
Customer: My bill is wrong again. This is the third time.
Agent: I'm sorry about that. Let me look into it.
Agent: I can see two incorrect charges. I'll refund both now.
Customer: Fine. I hope it's actually fixed this time.
Agent: I've also flagged your account for priority review.
Customer: Okay."""
    },
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_example1",
                "type": "function",
                "function": {
                    "name": "generate_call_summary",
                    "arguments": '{"issue": "Customer received incorrect billing charges for the third consecutive time", "resolution": "Agent refunded two incorrect charges and flagged account for priority review", "sentiment": "negative", "next_best_action": "Priority follow-up within 48 hours — third billing error indicates systemic account issue and high churn risk", "escalation_required": false}'
                }
            }
        ]
    },
    # ← ADD THIS — tool response completing the conversation turn
    {
        "role": "tool",
        "tool_call_id": "call_example1",
        "content": "Summary generated successfully."
    }
]

async def generate_call_summary_cot(transcript: str) -> dict:
    log.info(f"generate_call_summary_cot | transcript_len={len(transcript)} | calling LLM with CoT")

    messages = [
        {"role": "system", "content": COT_SYSTEM_PROMPT},
        # Few-shot example
        *FEW_SHOT_EXAMPLES,
        # Real transcript
        {"role": "user", "content": f"Transcript:\n{transcript}"}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,  # slightly higher — reasoning benefits from some flexibility
        max_tokens=800,   # more tokens — reasoning takes space
        messages=messages,
        tools=[{"type": "function", "function": SUMMARY_SCHEMA}],
        tool_choice={"type": "function", "function": {"name": "generate_call_summary"}}
    )

    tool_call = response.choices[0].message.tool_calls[0]
    summary = json.loads(tool_call.function.arguments)

    log.info(f"generate_call_summary_cot | tokens_used={response.usage.total_tokens} | sentiment={summary['sentiment']} | escalation={summary['escalation_required']}")
    return summary