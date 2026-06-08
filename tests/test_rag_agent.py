# test_rag_agent.py
from salesforce_agent import run_agent

queries = [
    "Customer wants to cancel their policy — what should I do?",
    "Customer says their policy was cancelled by mistake 2 weeks ago",
    "Customer is disputing a duplicate charge on their account",
    "Suspicious activity on account — customer didn't make the transaction",
]

for query in queries:
    print(f"\n{'='*55}")
    print(f"QUERY: {query}")
    print(f"{'='*55}")
    result = run_agent(query)
    print(f"AGENT: {result}")