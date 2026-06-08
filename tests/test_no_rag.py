# test_no_rag.py
# Same queries as test_rag_agent.py but WITHOUT RAG context
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

NO_RAG_SYSTEM_PROMPT = """
You are a Salesforce CRM agent for a contact center.
You help agents and supervisors manage Cases by taking actions on their behalf.
When given an instruction about a customer query, provide the Next Best Action.
Be concise and specific.
"""

def run_without_rag(instruction: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": NO_RAG_SYSTEM_PROMPT},
            {"role": "user",   "content": instruction}
        ]
    )
    return response.choices[0].message.content

queries = [
    "Customer wants to cancel their policy — what should I do?",
    "Customer says their policy was cancelled by mistake 2 weeks ago",
    "Customer is disputing a duplicate charge on their account",
    "Suspicious activity on account — customer didn't make the transaction",
]

print("\n=== WITHOUT RAG ===\n")
for query in queries:
    print(f"\n{'='*55}")
    print(f"QUERY: {query}")
    print(f"{'='*55}")
    result = run_without_rag(query)
    print(f"AGENT: {result}")