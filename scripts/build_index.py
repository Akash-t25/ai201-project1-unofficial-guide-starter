# HOW TO RUN THIS PROJECT
# 1. Create and activate a virtual environment:
#      python -m venv .venv
#      source .venv/bin/activate   (Mac/Linux)
#      .venv\Scripts\activate      (Windows)
# 2. Install dependencies:
#      pip install -r requirements.txt
# 3. Copy .env.example to .env and add your Groq API key:
#      cp .env.example .env
#      (Edit .env and replace 'your_key_here' with your actual key)
#      Get a free key at: https://console.groq.com
# 4. Build the index (run once):
#      python scripts/build_index.py
# 5. Launch the app:
#      python app.py
#      Then open: http://localhost:7860

"""One-shot pipeline: ingest -> chunk -> embed -> store, with verification.

Run from the repo root: ``python scripts/build_index.py``
"""

import os
import sys

# Make the src/ package importable when running this script from the repo root.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from ingest import load_and_clean
from chunk import chunk_documents, inspect_chunks
from embed import get_or_create_collection, embed_and_store, collection_info
from retrieve import get_retriever, retrieve

DATA_DIR = os.path.join(REPO_ROOT, "data", "raw")
PERSIST_DIR = os.path.join(REPO_ROOT, "chroma_db")

TEST_QUERIES = [
    "What do students say about Professor Mehta's exams?",
    "How hard is Operating Systems with Professor Kim?",
    "Which CS professor gives the most useful feedback?",
]


def main() -> None:
    print("=" * 70)
    print("BUILDING THE UNOFFICIAL GUIDE INDEX")
    print("=" * 70)

    # 1. Load and clean.
    print("\n[1/5] Loading and cleaning documents...")
    docs = load_and_clean(DATA_DIR)

    # 2. Chunk.
    print("\n[2/5] Chunking documents...")
    chunks = chunk_documents(docs)

    # 3. Inspect a sample.
    print("\n[3/5] Inspecting sample chunks...")
    inspect_chunks(chunks, n=5)

    # 4. Embed and store.
    print("\n[4/5] Embedding and storing in ChromaDB...")
    collection = get_or_create_collection(PERSIST_DIR)
    embed_and_store(chunks, collection)
    print("Collection info:", collection_info(collection))

    # 5. Verify retrieval with a few test queries.
    print("\n[5/5] Verifying retrieval...")
    model, collection = get_retriever(PERSIST_DIR)
    for query in TEST_QUERIES:
        print(f"\nQuery: {query}")
        results = retrieve(query, model, collection, top_k=3)
        for r in results:
            preview = r["text"].replace("\n", " ")[:100]
            print(f"  [{r['source']}] dist={r['distance']:.4f}  {preview}...")

    # Success summary.
    print("\n" + "=" * 70)
    print("SUCCESS")
    print(f"  Documents loaded : {len(docs)}")
    print(f"  Chunks stored    : {len(chunks)}")
    print(f"  ChromaDB path    : {PERSIST_DIR}")
    print("  Next step        : run `python app.py` to launch the web UI")
    print("=" * 70)


if __name__ == "__main__":
    main()
