"""Embedding and ChromaDB storage for The Unofficial Guide.

Uses the all-MiniLM-L6-v2 SentenceTransformer model (local, fast, good for
short text) and stores vectors in a persistent ChromaDB collection.
"""

import chromadb
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "unofficial_guide"


def get_or_create_collection(persist_dir: str = "chroma_db"):
    """Return the persistent ChromaDB collection, creating it if needed."""
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return collection


def embed_and_store(chunks: list[dict], collection, model_name: str = "all-MiniLM-L6-v2") -> None:
    """Embed all chunk texts in one batch and store them in ChromaDB."""
    model = SentenceTransformer(model_name)

    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)

    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=[{"source": c["source"]} for c in chunks],
    )

    print(f"Stored {len(chunks)} embeddings in collection '{collection.name}'")


def collection_info(collection) -> dict:
    """Return basic info about a collection."""
    return {"count": collection.count(), "name": collection.name}


if __name__ == "__main__":
    from ingest import load_and_clean
    from chunk import chunk_documents

    docs = load_and_clean("data/raw")
    chunked = chunk_documents(docs)
    coll = get_or_create_collection()
    embed_and_store(chunked, coll)
    print(collection_info(coll))
