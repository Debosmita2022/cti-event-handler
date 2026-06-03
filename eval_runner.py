# eval_runner.py
import asyncio
import json
from llm import generate_call_summary_structured, generate_call_summary_cot, client
from eval_transcripts import TRANSCRIPTS
from logger import get_logger

log = get_logger("eval")

JUDGE_PROMPT = """
You are an expert evaluator of contact center AI systems.

You will be given:
1. A call transcript
2. An AI-generated call summary with NBA suggestion

Score the summary on four dimensions, each 1-10:

- issue_accuracy: Did it correctly identify the customer's core problem?
  (1=completely wrong, 10=perfectly accurate)

- nba_specificity: Is the next_best_action concrete and actionable?
  (1=vague generic action, 10=specific, measurable, time-bound action)

- sentiment_correctness: Did it correctly read the customer's emotional tone?
  (1=completely wrong, 10=exactly right)

- escalation_accuracy: Did it correctly flag or not flag escalation?
  (1=completely wrong, 10=exactly right)

Respond with ONLY a JSON object:
{
  "issue_accuracy": <1-10>,
  "nba_specificity": <1-10>,
  "sentiment_correctness": <1-10>,
  "escalation_accuracy": <1-10>,
  "overall": <average of the four>,
  "reasoning": "<one sentence explaining the biggest strength or weakness>"
}
"""

async def judge_summary(transcript: str, summary: dict, expected: dict) -> dict:
    prompt = f"""
Transcript:
{transcript}

AI Summary:
{json.dumps(summary, indent=2)}

Expected sentiment: {expected['expected_sentiment']}
Expected escalation: {expected['expected_escalation']}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,  # zero — judge must be deterministic
        max_tokens=300,
        messages=[
            {"role": "system", "content": JUDGE_PROMPT},
            {"role": "user",   "content": prompt}
        ]
    )
    raw = response.choices[0].message.content
    clean = raw.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:-1])
    return json.loads(clean)


async def run_eval():
    results = []

    for t in TRANSCRIPTS:
        log.info(f"eval | transcript={t['id']} | type={t['type']}")

        # Run both variants
        direct  = await generate_call_summary_structured(t["transcript"])
        cot     = await generate_call_summary_cot(t["transcript"])

        # Judge both
        direct_score = await judge_summary(t["transcript"], direct, t)
        cot_score    = await judge_summary(t["transcript"], cot, t)

        results.append({
            "id":           t["id"],
            "type":         t["type"],
            "direct_score": direct_score,
            "cot_score":    cot_score,
            "direct_nba":   direct["next_best_action"],
            "cot_nba":      cot["next_best_action"],
        })

        log.info(f"eval | {t['id']} | direct={direct_score['overall']} | cot={cot_score['overall']}")

    return results


async def print_findings(results: list):
    print("\n" + "="*60)
    print("EVAL RESULTS — Direct vs Chain-of-Thought")
    print("="*60)

    # Per-transcript scores
    print(f"\n{'ID':<6} {'Type':<25} {'Direct':>8} {'CoT':>8} {'Winner':>8}")
    print("-"*60)

    direct_totals = {"issue_accuracy":0,"nba_specificity":0,"sentiment_correctness":0,"escalation_accuracy":0,"overall":0}
    cot_totals    = {"issue_accuracy":0,"nba_specificity":0,"sentiment_correctness":0,"escalation_accuracy":0,"overall":0}

    for r in results:
        winner = "CoT" if r["cot_score"]["overall"] > r["direct_score"]["overall"] else "Direct" if r["direct_score"]["overall"] > r["cot_score"]["overall"] else "Tie"
        print(f"{r['id']:<6} {r['type']:<25} {r['direct_score']['overall']:>8.1f} {r['cot_score']['overall']:>8.1f} {winner:>8}")

        for k in direct_totals:
            direct_totals[k] += r["direct_score"][k]
            cot_totals[k]    += r["cot_score"][k]

    n = len(results)
    print("-"*60)
    print(f"\n{'AVERAGES':<31} {direct_totals['overall']/n:>8.1f} {cot_totals['overall']/n:>8.1f}")

    print(f"\n{'Dimension':<25} {'Direct':>8} {'CoT':>8}")
    print("-"*45)
    for k in ["issue_accuracy","nba_specificity","sentiment_correctness","escalation_accuracy"]:
        print(f"{k:<25} {direct_totals[k]/n:>8.1f} {cot_totals[k]/n:>8.1f}")

    # NBA comparison on most interesting cases
    print("\n--- NBA Comparison (selected) ---")
    for r in results[:3]:
        print(f"\n[{r['id']}] {r['type']}")
        print(f"  Direct: {r['direct_nba']}")
        print(f"  CoT:    {r['cot_nba']}")


async def main():
    print("Running evals — 10 transcripts × 2 variants × 1 judge = 30 API calls")
    print("This will take about 60-90 seconds...\n")
    results = await run_eval()
    await print_findings(results)

asyncio.run(main())