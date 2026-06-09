"""Gradio web UI for The Unofficial Guide.

Run with: ``python app.py`` (after building the index with
``python scripts/build_index.py``). Opens at http://localhost:7860.
"""

import os
import sys

# Make the src/ package importable.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

import gradio as gr

from generate import ask


def answer_question(question: str):
    """Handler wired to the Ask button and the textbox submit event.

    Returns (answer_text, sources_markdown, debug_chunks_text).
    """
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", "", ""

    result = ask(question)

    answer = result["answer"]
    sources = "\n".join(f"- {s}" for s in result["sources"])

    debug_lines = []
    for c in result["chunks"]:
        debug_lines.append(
            f"[Source: {c['source']}]  (distance: {c['distance']:.4f})\n{c['text']}"
        )
    debug = "\n\n---\n\n".join(debug_lines)

    return answer, sources, debug


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown("# The Unofficial Guide — CS Department")
    gr.Markdown(
        "Ask questions about CS professors, courses, and student life. "
        "Answers are grounded in real student-written documents."
    )

    question_box = gr.Textbox(label="Your question", placeholder="e.g. Does Professor Mehta curve exams?")
    ask_btn = gr.Button("Ask", variant="primary")

    answer_box = gr.Textbox(label="Answer", lines=10, interactive=False)
    sources_box = gr.Textbox(label="Retrieved from", lines=4, interactive=False)

    with gr.Accordion("Retrieved chunks (debug view)", open=False):
        debug_box = gr.Textbox(label="Chunks + distances", lines=12, interactive=False)

    gr.Examples(
        examples=[
            "What do students say about Professor Chen's grading style?",
            "How should I prepare for Professor Mehta's midterm?",
            "Is Machine Learning with Okafor recommended for undergrads?",
            "What happens in OS with Kim if I don't start assignments early?",
            "Which professor is best for someone who wants to go into industry?",
        ],
        inputs=question_box,
    )

    outputs = [answer_box, sources_box, debug_box]
    ask_btn.click(answer_question, inputs=question_box, outputs=outputs)
    question_box.submit(answer_question, inputs=question_box, outputs=outputs)


if __name__ == "__main__":
    demo.launch()
