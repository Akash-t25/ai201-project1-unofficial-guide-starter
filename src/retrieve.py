"""Semantic retrieval for The Unofficial Guide.

Loads the embedding model and the existing ChromaDB collection, embeds a query,
and returns the most relevant chunks ranked by distance (lower = more similar).
"""

import chromadb
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "unofficial_guide"


def get_retriever(persist_dir: str = "chroma_db", model_name: str = "all-MiniLM-L6-v2"):
    """Load the embedding model and the persistent collection.

    Returns a ``(model, collection)`` tuple.
    """
    model = SentenceTransformer(model_name)
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_collection(name=COLLECTION_NAME)
    return model, collection


def retrieve(query: str, model, collection, top_k: int = 5) -> list[dict]:
    """Embed ``query`` and return the top_k most relevant chunks.

    Each result is ``{"text": doc, "source": source, "distance": distance}``,
    sorted by distance ascending (most relevant first).
    """
    query_embedding = model.encode([query]).tolist()
    raw = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    documents = raw["documents"][0]
    metadatas = raw["metadatas"][0]
    distances = raw["distances"][0]

    results = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        results.append(
            {
                "text": doc,
                "source": meta["source"],
                # Cast to float defensively so sorting is always numeric.
                "distance": float(dist),
            }
        )

    results.sort(key=lambda r: r["distance"])
    return results


def format_context(results: list[dict]) -> str:
    """Join retrieved chunks into a single context string for the LLM prompt."""
    blocks = []
    for r in results:
        blocks.append(f"[Source: {r['source']}]\n{r['text']}")
    return "\n\n---\n\n".join(blocks)


if __name__ == "__main__":
    model, collection = get_retriever()
    hits = retrieve("What do students say about Professor Mehta's exams?", model, collection)
    for h in hits:
        print(f"[{h['source']}] dist={h['distance']:.4f}")
        print(h["text"][:120], "...\n")
