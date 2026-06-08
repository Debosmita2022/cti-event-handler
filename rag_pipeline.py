# rag_pipeline.py
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from knowledge_base import DOCUMENTS
from logger import get_logger

log = get_logger("rag")

# Load embedding model — runs locally, no API key needed
MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

# Build index at startup
log.info(f"rag | building index | documents={len(DOCUMENTS)} | model={MODEL_NAME}")

# Generate embeddings for all documents
texts = [f"{doc['title']}\n{doc['content']}" for doc in DOCUMENTS]
embeddings = model.encode(texts, show_progress_bar=False)
embeddings = np.array(embeddings).astype("float32")

# Normalise for cosine similarity
faiss.normalize_L2(embeddings)

# Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)  # Inner Product = cosine similarity after normalisation
index.add(embeddings)

log.info(f"rag | index built | dimension={dimension} | vectors={index.ntotal}")


def retrieve(query: str, top_k: int = 2) -> list[dict]:
    """
    Retrieve the most relevant policy documents for a given query.
    Returns top_k documents with similarity scores.
    """
    log.info(f"retrieve | query={query[:60]} | top_k={top_k}")

    # Embed the query
    query_embedding = model.encode([query], show_progress_bar=False)
    query_embedding = np.array(query_embedding).astype("float32")
    faiss.normalize_L2(query_embedding)

    # Search
    scores, indices = index.search(query_embedding, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        doc = DOCUMENTS[idx].copy()
        doc["similarity_score"] = round(float(score), 3)
        results.append(doc)
        log.info(f"retrieve | matched | id={doc['id']} | title={doc['title'][:50]} | score={doc['similarity_score']}")

    return results


def retrieve_context(query: str, top_k: int = 2) -> str:
    """
    Returns retrieved documents as a formatted string for LLM context injection.
    """
    docs = retrieve(query, top_k)
    if not docs:
        return "No relevant policy documents found."

    context = "RELEVANT POLICY DOCUMENTS:\n\n"
    for doc in docs:
        context += f"[{doc['id']}] {doc['title']}\n"
        context += f"{doc['content'].strip()}\n\n"
    return context