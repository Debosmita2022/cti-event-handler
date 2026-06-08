# test_rag.py
from rag_pipeline import retrieve, retrieve_context

queries = [
    "Customer wants to cancel their insurance policy",
    "Customer asking about what their policy covers",
    "I was charged twice on my account",
    "Suspicious transaction on my account — possible fraud",
    "Customer wants to renew but premium went up a lot",
    "Customer wants to cancel just the add-on not the whole policy",
    "Policy was cancelled by mistake — customer wants it back",
]

print("\n=== RAG Retrieval Test ===\n")
for query in queries:
    print(f"Query: {query}")
    results = retrieve(query, top_k=1)
    print(f"  → [{results[0]['id']}] {results[0]['title']} (score={results[0]['similarity_score']})")
    print()