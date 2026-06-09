"""Chunking strategy for The Unofficial Guide.

We use RecursiveCharacterTextSplitter (not the plain CharacterTextSplitter)
because it respects natural boundaries — paragraphs, then lines, then
sentences — before falling back to a hard character cut. That matters for this
corpus, where the atomic unit of meaning is a single short student review.

chunk_size=400 chars fits 2-4 student review sentences, which is the natural
atomic unit of this corpus (one complete opinion about one professor).
chunk_overlap=80 prevents splitting mid-thought across boundaries, so a rating
and its explanation usually stay together.
"""

import random

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(
    documents: list[dict],
    chunk_size: int = 400,
    chunk_overlap: int = 80,
) -> list[dict]:
    """Split each document into overlapping character chunks.

    Each chunk dict is ``{"chunk_id": f"{source}_{i}", "source": source, "text": chunk_text}``.
    Chunks shorter than 30 characters are filtered out as noise.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks: list[dict] = []
    for doc in documents:
        source = doc["source"]
        pieces = splitter.split_text(doc["text"])
        for i, piece in enumerate(pieces):
            piece = piece.strip()
            if len(piece) < 30:
                continue
            chunks.append(
                {
                    "chunk_id": f"{source}_{i}",
                    "source": source,
                    "text": piece,
                }
            )

    print(f"Created {len(chunks)} chunks from {len(documents)} documents")
    return chunks


def inspect_chunks(chunks: list[dict], n: int = 5) -> None:
    """Print ``n`` random chunks with their source and character length.

    Used for manual inspection during development to sanity-check that chunk
    boundaries land in reasonable places.
    """
    sample = random.sample(chunks, min(n, len(chunks)))
    print(f"\n--- Inspecting {len(sample)} random chunks ---")
    for chunk in sample:
        print(f"\n[{chunk['chunk_id']}] ({len(chunk['text'])} chars)")
        print(chunk["text"])
    print("\n--- end inspection ---\n")


if __name__ == "__main__":
    from ingest import load_and_clean

    docs = load_and_clean("data/raw")
    chunked = chunk_documents(docs)
    inspect_chunks(chunked)
