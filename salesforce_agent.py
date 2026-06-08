# salesforce_agent.py
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from salesforce_cases import (
    get_sf_connection, get_case_by_id, get_open_cases,
    create_case, update_case_with_summary, close_case
)
from logger import get_logger
from rag_pipeline import retrieve_context

import time

load_dotenv()
log = get_logger("salesforce_agent")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Tool definitions — what actions the agent can take ──────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_open_cases",
            "description": "Get all open Salesforce Cases. Use when asked about pending, open, or active cases.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_case_by_number",
            "description": "Get a specific Case by its case number (e.g. 00001026). Use when a specific case is mentioned.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_number": {
                        "type": "string",
                        "description": "The case number e.g. 00001026"
                    }
                },
                "required": ["case_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_case",
            "description": "Escalate a Case to high priority. Use when asked to escalate, prioritise urgently, or flag for immediate attention.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "The Salesforce Case ID (starts with 500)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for escalation"
                    }
                },
                "required": ["case_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_case_with_resolution",
            "description": "Close a Case with a resolution note. Use when asked to close, resolve, or mark as done.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "The Salesforce Case ID (starts with 500)"
                    },
                    "resolution": {
                        "type": "string",
                        "description": "Resolution summary"
                    }
                },
                "required": ["case_id", "resolution"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_new_case",
            "description": "Create a new Salesforce Case. Use when asked to log, create, or open a new case.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Case subject/title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Case description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["Low", "Medium", "High"],
                        "description": "Case priority"
                    }
                },
                "required": ["subject", "description", "priority"]
            }
        }
    }
]

AGENT_SYSTEM_PROMPT = """
You are a Salesforce CRM agent for a contact center.
You help agents and supervisors manage Cases by taking actions on their behalf.

You have access to tools to read, create, update, and close Salesforce Cases.
You also receive relevant policy documents to ground your responses.

When given an instruction:
1. Use the policy documents provided to inform your Next Best Action recommendation
2. Use the appropriate tool to execute the CRM action
3. After executing, confirm what was done and include a policy-grounded NBA suggestion

Be concise. Always reference the relevant policy when making NBA suggestions.
"""

def execute_tool(tool_name: str, tool_args: dict) -> str:
    """Executes the tool the LLM decided to call. Returns result as string."""
    sf = get_sf_connection()
    log.info(f"execute_tool | tool={tool_name} | args={tool_args}")

    if tool_name == "get_open_cases":
        cases = get_open_cases(sf)
        if not cases:
            return "No open cases found."
        result = f"Found {len(cases)} open cases:\n"
        for c in cases:
            result += f"- {c['CaseNumber']}: {c['Subject'][:60]} [{c['Priority']}]\n"
        return result

    elif tool_name == "get_case_by_number":
        case_number = tool_args["case_number"]
        result = sf.query(f"SELECT Id, CaseNumber, Subject, Status, Priority, Description FROM Case WHERE CaseNumber = '{case_number}' LIMIT 1")
        if result['totalSize'] == 0:
            return f"Case {case_number} not found."
        case = result['records'][0]
        return f"Case {case['CaseNumber']}: {case['Subject']} | Status: {case['Status']} | Priority: {case['Priority']}"

    elif tool_name == "escalate_case":
        case_id = tool_args["case_id"]
        reason  = tool_args["reason"]
        sf.Case.update(case_id, {
            "Priority": "High",
            "Status":   "Escalated",
            "Description": f"ESCALATED: {reason}"
        })
        return f"Case {case_id} escalated to High priority. Status set to Escalated. Reason: {reason}"

    elif tool_name == "close_case_with_resolution":
        case_id    = tool_args["case_id"]
        resolution = tool_args["resolution"]
        close_case(sf, case_id, resolution)
        return f"Case {case_id} closed. Resolution: {resolution}"

    elif tool_name == "create_new_case":
        case_id = create_case(
            sf,
            subject=tool_args["subject"],
            description=tool_args["description"],
            priority=tool_args["priority"]
        )
        return f"New case created with ID {case_id}. Subject: {tool_args['subject']}"

    else:
        return f"Unknown tool: {tool_name}"



def run_agent(instruction: str, retries: int = 3) -> str:
    for attempt in range(1, retries + 1):
        try:
            return _run_agent_once(instruction)
        except Exception as e:
            if attempt < retries:
                log.warning(f"run_agent | attempt={attempt} | error={e} | retrying in 2s")
                time.sleep(2)
            else:
                raise


def _run_agent_once(instruction: str) -> str:
    
    log.info(f"run_agent | instruction={instruction[:80]}")

    # Retrieve relevant policy documents
    policy_context = retrieve_context(instruction, top_k=2)
    log.info(f"run_agent | rag_context_retrieved | length={len(policy_context)}")

    # Inject policy context into the user message
    enriched_instruction = f"""
{instruction}

{policy_context}

Use the policy documents above to ground your NBA recommendation.
"""

    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user",   "content": enriched_instruction}
    ]

    # Rest of the function stays the same
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )

    message = response.choices[0].message

    if not message.tool_calls:
        log.info(f"run_agent | no_tool_called | direct_response")
        return message.content

    tool_call   = message.tool_calls[0]
    tool_name   = tool_call.function.name
    tool_args   = json.loads(tool_call.function.arguments)

    log.info(f"run_agent | tool_selected={tool_name} | args={tool_args}")
    tool_result = execute_tool(tool_name, tool_args)
    log.info(f"run_agent | tool_result={tool_result[:100]}")

    messages.append({"role": "assistant", "content": None, "tool_calls": message.tool_calls})
    messages.append({
        "role":         "tool",
        "tool_call_id": tool_call.id,
        "content":      tool_result
    })

    final = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=messages,
        tools=TOOLS
    )

    result = final.choices[0].message.content
    if result is None:
    # Model called another tool — extract tool result as response
        result = tool_result
        log.info(f"run_agent | complete | result={result[:100]}")
    return result