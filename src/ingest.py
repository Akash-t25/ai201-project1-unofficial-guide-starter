"""Document loading and cleaning for The Unofficial Guide.

Reads the raw student-written .txt files from data/raw/, normalizes them, and
returns plain dicts ready for chunking. No third-party dependencies needed here —
just the standard library.
"""

import os
import re


def load_documents(data_dir: str) -> list[dict]:
    """Walk ``data_dir`` and load every .txt file.

    Returns a list of dicts shaped like ``{"source": filename, "text": raw_text}``.
    """
    documents = []
    for root, _dirs, files in os.walk(data_dir):
        for filename in sorted(files):
            if not filename.endswith(".txt"):
                continue
            path = os.path.join(root, filename)
            with open(path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            documents.append({"source": filename, "text": raw_text})

    print(f"Loaded {len(documents)} documents from {data_dir}")
    return documents


def clean_text(text: str) -> str:
    """Normalize a raw document string.

    - strip leading/trailing whitespace
    - collapse multiple blank lines into a single blank line
    - drop separator-only lines (just dashes or underscores)
    - normalize unicode quotes to straight quotes
    """
    # Normalize unicode quotes to straight quotes.
    replacements = {
        "‘": "'",  # left single quote
        "’": "'",  # right single quote / apostrophe
        "“": '"',  # left double quote
        "”": '"',  # right double quote
    }
    for fancy, plain in replacements.items():
        text = text.replace(fancy, plain)

    # Remove artifact separator lines (e.g. "----" or "____").
    kept_lines = []
    for line in text.splitlines():
        if re.fullmatch(r"\s*[-_]{2,}\s*", line):
            continue
        kept_lines.append(line.rstrip())
    text = "\n".join(kept_lines)

    # Collapse 3+ consecutive newlines down to a single blank line.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def load_and_clean(data_dir: str) -> list[dict]:
    """Load documents from ``data_dir`` then clean each one's text.

    Prints a word count per document and returns the cleaned list.
    """
    documents = load_documents(data_dir)
    for doc in documents:
        doc["text"] = clean_text(doc["text"])
        word_count = len(doc["text"].split())
        print(f"  {doc['source']}: {word_count} words")
    return documents


if __name__ == "__main__":
    load_and_clean("data/raw")
