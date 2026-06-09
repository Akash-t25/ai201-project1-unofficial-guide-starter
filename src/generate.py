"""Grounded answer generation for The Unofficial Guide.

Wraps the Groq LLM (llama-3.3-70b-versatile) with a strict system prompt that
forces the model to answer ONLY from the retrieved context. The ``ask()``
function is the self-contained end-to-end entry point used by app.py.
"""

import os

from dotenv import load_dotenv
from groq import Groq

SYSTEM_PROMPT = (
    "You are a helpful assistant for students navigating university life. \n"
    "Answer questions using ONLY the information provided in the documents below. \n"
    "Do not use your general knowledge or training data.\n"
    "If the documents do not contain enough information to answer the question, \n"
    'say exactly: "I don\'t have enough information in my sources to answer that."\n'
    'Always end your answer with a "Sources:" line listing the document filenames you drew from.'
)


def get_groq_client() -> Groq:
    """Load the .env file and return an authenticated Groq client."""
    load_dotenv()
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def build_prompt(query: str, context: str) -> list[dict]:
    """Build the messages list for the Groq chat completion call."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Documents:\n\n{context}\n\nQuestion: {query}",
        },
    ]


def generate_answer(query: str, context: str, client) -> str:
    """Call the Groq LLM and return the answer text."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=build_prompt(query, context),
        max_tokens=600,
        temperature=0.2,
    )
    return response.choices[0].message.content


def ask(query: str, top_k: int = 5) -> dict:
    """End-to-end question answering: retrieve, ground, and generate.

    Self-contained: loads the retriever, collection, and Groq client internally
    so callers (e.g. app.py) only need to import this one function.

    Returns ``{"answer": str, "sources": list[str], "chunks": list[dict]}``.
    """
    # Imported here to keep this module importable even before the index exists.
    from retrieve import get_retriever, retrieve, format_context

    model, collection = get_retriever()
    chunks = retrieve(query, model, collection, top_k=top_k)
    context = format_context(chunks)

    client = get_groq_client()
    answer = generate_answer(query, context, client)

    # Unique source filenames, preserving retrieval order.
    seen = set()
    sources = []
    for c in chunks:
        if c["source"] not in seen:
            seen.add(c["source"])
            sources.append(c["source"])

    return {"answer": answer, "sources": sources, "chunks": chunks}


if __name__ == "__main__":
    result = ask("Does Professor Mehta curve exams in CS101?")
    print(result["answer"])
    print("\nSources:", result["sources"])
