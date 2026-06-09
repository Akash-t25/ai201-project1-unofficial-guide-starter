# The Unofficial Guide — CS Department

A Retrieval-Augmented Generation (RAG) system that answers questions about CS professors and courses using **real student-written content** — the kind of candid advice found on Rate My Professors, Reddit, and class Discord/Slack servers. Ask it whether a professor curves, how long an assignment actually takes, or which class to avoid stacking with another, and it answers **only** from a corpus of student reviews and guides, citing its sources.

---

## 1. Project overview

The Unofficial Guide ingests ten student-written documents about a CS department, chunks and embeds them, and serves grounded answers through a Gradio web UI. The domain is **student-generated knowledge about CS professors and courses** — decision-grade information (curves, workload, prerequisites, exam style) that official advisors, professor bios, and syllabi don't capture. Every answer is generated strictly from retrieved document text and ends with a `Sources:` line, so users can trace any claim back to where it came from.

---

## 2. Domain and document sources

The corpus lives in `data/raw/` as ten `.txt` files:

1. **prof_mehta_cs101.txt** — Student reviews of Prof. Mehta's intro CS course (recorded lectures, generous curve, time-pressured exams, autograder bugs, research-talk extra credit).
2. **prof_chen_ds301.txt** — Reviews of Prof. Chen's Data Structures course (hard grader, no curve, 10–15 hour assignments, handwritten pseudocode exams, generous partial credit).
3. **prof_okafor_ml450.txt** — Reviews of Prof. Okafor's Machine Learning course (research-focused, strong-math prerequisite, 70% project grade, team projects, paper readings).
4. **prof_rodriguez_web220.txt** — Reviews of Prof. Rodriguez's Web Development course (project-based, React/Node/PostgreSQL, 15% participation, strict code review, responsive on Slack).
5. **prof_kim_os410.txt** — Reviews of Prof. Kim's Operating Systems course (hardest CS course, 20+ hour kernel assignments, open-note exams, live coding, strict prereq).
6. **cs_dept_survival_guide.txt** — An unofficial student-written department survival guide (registration lottery, closed sections, helpful TAs, course sequencing, pitfalls).
7. **reddit_cs_megathread.txt** — Compiled excerpts from a "what I wish I knew" subreddit megathread (workload warnings, regrade tips, recruiting timeline, honor-code advice).
8. **prof_mehta_office_hours_tips.txt** — Targeted tips for Mehta's office hours and CS101 (timing, Socratic method, TA Marcus, Friday sessions).
9. **exam_prep_cs301.txt** — Crowdsourced exam-prep notes for Chen's Data Structures (frequent midterm topics, heap/hash-table mistakes, how Chen grades pseudocode, DP on every final).
10. **grade_distribution_notes.txt** — Informal observations on grade distributions across the five courses (averages, OS410's D/F rate, pass/fail and late-drop advice).

---

## 3. Chunking strategy and reasoning

**`chunk_size = 400` characters, `chunk_overlap = 80` characters**, using LangChain's `RecursiveCharacterTextSplitter`.

Nearly every document is a list of short **opinion units** — one student review or one piece of advice, typically 2–5 sentences. 400 characters is about that length, so each chunk captures **one complete thought about one professor** (the claim plus its justification). The 80-character overlap keeps a review's verdict attached to its explanation when a boundary lands mid-sentence — e.g. so "the curve is generous —" and "around 10 points" stay in the same retrievable unit.

Chunks under 30 characters are filtered out as noise. The recursive splitter is used over the plain `CharacterTextSplitter` because it respects paragraph → line → sentence boundaries before resorting to a hard character cut, which keeps individual reviews intact.

---

## 4. Sample chunks

Representative chunks produced by the pipeline (source filename labeled):

**Sample 1 — `prof_mehta_cs101.txt`**
> The curve is real and it's generous — I think it was around 10 points the semester I took it. I went into the final convinced I bombed it and ended up with a B+. Office hours are where she shines. Go even if you think your question is dumb.

**Sample 2 — `prof_chen_ds301.txt`**
> The coding assignments are brutal — budget 10 to 15 hours each, no joke. I thought I was fast and they still ate my whole weekend. Start them the day they're posted.

**Sample 3 — `prof_okafor_ml450.txt`**
> Heads up: he assumes a strong math background. Linear algebra and probability are not optional. If you're shaky on eigenvectors and conditional probability you will drown in the first three weeks.

**Sample 4 — `prof_rodriguez_web220.txt`**
> Participation counts 15% of the grade, so show up and engage. She brings in guest speakers from local tech companies almost every other week and those sessions are genuinely worth attending.

**Sample 5 — `prof_kim_os410.txt`**
> START EARLY. The assignments take 20+ hours each and that's if nothing goes wrong, which it always does. A friend started the scheduler assignment two days before it was due and ended up taking a zero.

---

## 5. Embedding model

Embeddings use **`all-MiniLM-L6-v2`** via `sentence-transformers`. It is **local** (no API cost, no network dependency), **fast** (384-dimensional, runs on a laptop CPU), and trained on sentence-level semantic similarity — a strong match for our short, review-sized chunks.

**Production tradeoffs** a real deployment would weigh:
- **Accuracy:** a hosted model like OpenAI `text-embedding-3-large` would likely retrieve more precisely, at the cost of per-query billing and a network dependency.
- **Context length:** MiniLM truncates around 256 tokens; longer documents would need a model with a larger context window or more careful chunking.
- **Multilingual support:** for international students writing in other languages, a multilingual model (e.g. `paraphrase-multilingual-MiniLM`) would be necessary.
- **Cost at scale:** local MiniLM is free per query; a hosted embedding API bills on every query and every re-index, which compounds quickly campus-wide.

---

## 6. Retrieval test results

The three queries `scripts/build_index.py` runs against the built index, with the **actual** top chunks and ChromaDB distances returned (lower = closer):

**Query A: "What do students say about Professor Mehta's exams?"**
- `prof_mehta_cs101.txt` (0.706) → "Review 1: Honestly one of the best intro professors in the department. Mehta explains everything clearly..."
- `prof_rodriguez_web220.txt` (0.812) → "Review 2: No traditional exams at all. It's entirely project-based..."
- `prof_mehta_cs101.txt` (0.924) → "Review 6: Slightly negative take: the time pressure on exams is rough..."

*Why relevant:* the top and third chunks are Mehta-specific (the third directly addresses exam time-pressure, the heart of the question). The intrusion at rank 2 is instructive — a Rodriguez review ranked highly purely because it contains the word "exams" (saying she has *none*), a reminder that semantic search keys on the term even when the professor is wrong.

**Query B: "How hard is Operating Systems with Professor Kim?"**
- `prof_kim_os410.txt` (0.692) → "Professor Jae-Won Kim — Operating Systems (OS410)... Review 1: OS410 is widely considered the hardest CS course..."
- `prof_kim_os410.txt` (0.993) → "Review 4: Kim does live coding in class and it's the best part..."
- `prof_kim_os410.txt` (1.008) → "Review 7: Worth it if you want a systems or infrastructure role..."

*Why relevant:* all three top chunks are correctly from the Kim/OS410 document, and the closest one opens with the exact "hardest CS course" framing that answers the difficulty question. Clean, on-target retrieval with a clear distance gap between rank 1 and the rest.

**Query C: "Which CS professor gives the most useful feedback?"**
- `reddit_cs_megathread.txt` (0.887) → "r/UniversityCS Megathread: 'What do you wish you knew before taking upper-division CS?'..."
- `reddit_cs_megathread.txt` (0.909) → "u/mehta_stan: Take Mehta for CS101. Recorded lectures, generous curve (~10 pts)..."
- `prof_mehta_cs101.txt` (0.932) → "Review 8: Took this as a non-major to fulfill a requirement..."

*Why relevant:* this abstract query ("useful feedback") has no exact keyword in the corpus, and the larger distances (~0.9) reflect that — there's no single chunk that cleanly answers it, so the retriever returns broad advice-oriented chunks. This illustrates a soft query where semantic matching degrades gracefully rather than failing outright.

---

## 7. Grounded generation

Generation uses Groq's **`llama-3.3-70b-versatile`** with a strict grounding system prompt. The prompt forces the model to answer **only** from the retrieved documents, to refuse with an exact sentence when the documents are insufficient, and to always cite sources.

**Exact system prompt:**
```
You are a helpful assistant for students navigating university life. 
Answer questions using ONLY the information provided in the documents below. 
Do not use your general knowledge or training data.
If the documents do not contain enough information to answer the question, 
say exactly: "I don't have enough information in my sources to answer that."
Always end your answer with a "Sources:" line listing the document filenames you drew from.
```

**Why `temperature=0.2`:** a low temperature makes the model nearly deterministic and strongly favors the highest-probability continuation, which here is the text supported by the provided context. Higher temperatures encourage "creative" continuations that drift toward the model's parametric knowledge — exactly the hallucination risk this system is designed to avoid. Combined with the ONLY-from-documents instruction, low temperature keeps answers anchored to the retrieved chunks.

---

## 8. Example responses

**Example 1 (in scope):**
> **Q:** Does Professor Mehta curve exams in CS101?
> **A:** Yes — students report that Professor Mehta curves CS101, and the curve is described as generous, around 10 points. One reviewer went into the final thinking they had bombed it and still ended up with a B+ thanks to the curve.
> **Sources:** prof_mehta_cs101.txt, grade_distribution_notes.txt

**Example 2 (in scope):**
> **Q:** What happens in OS with Kim if I don't start assignments early?
> **A:** Students strongly warn to start early because the kernel assignments take 20+ hours each, and that's assuming nothing goes wrong. One reviewer mentions a friend who started a scheduler assignment two days before the deadline and ended up taking a zero.
> **Sources:** prof_kim_os410.txt, reddit_cs_megathread.txt

**Example 3 (out of scope — refusal):**
> **Q:** What is Professor Mehta's home address?
> **A:** I don't have enough information in my sources to answer that.

---

## 9. Query interface

The UI is a Gradio app (`app.py`) built with `gr.Blocks()`:

- **Your question** — text input for the user's question (also submits on Enter).
- **Ask** — button that runs the RAG pipeline.
- **Answer** — read-only box (10 lines) showing the grounded answer with its `Sources:` line.
- **Retrieved from** — read-only box listing the unique source filenames as a bulleted list.
- **Retrieved chunks (debug view)** — a collapsible accordion showing every retrieved chunk with its source and distance, for transparency/debugging.
- **Examples** — five clickable starter questions.

**Sample interaction transcript:**
```
Your question:  How should I prepare for Professor Mehta's midterm?

Answer:
Focus on loops and recursion — students say the midterm is basically those two
topics, and if you can trace a recursive function by hand you'll be fine. It's
worth rewatching the recorded recursion lectures, and going to office hours early
(the Friday session is less crowded) where Mehta uses a Socratic style to help
you reason through problems.
Sources: prof_mehta_cs101.txt, prof_mehta_office_hours_tips.txt

Retrieved from:
- prof_mehta_cs101.txt
- prof_mehta_office_hours_tips.txt
```

---

## 10. Evaluation report

Full per-question detail is in [`evaluation/report.md`](evaluation/report.md). Summary:

| # | Question | Expected answer | System response (summary) | Judgment |
|---|----------|-----------------|---------------------------|----------|
| Q1 | Does Professor Mehta curve exams in CS101? | Yes, ~10 points | Yes, generous curve around 10 points | **Accurate** |
| Q2 | How long do assignments take in Chen's course? | 10–15 hours each | 10–15 hours each, start early | **Accurate** |
| Q3 | Is ML450 suitable without strong math? | No — assumes linalg & probability | No; assumes strong linear algebra & probability | **Accurate** |
| Q4 | Participation % in Rodriguez's Web Dev? | 15% | 15% (but also volunteered unrelated code-review info) | **Partially accurate** |
| Q5 | Topic on every final in Chen's course? | Dynamic programming | Failed to surface DP; declined to answer | **Inaccurate** |

---

## 11. Failure case

**Q5 — "What topic appears on every final exam in Professor Chen's course?" (expected: dynamic programming).**

The fact *exists* in the corpus, intact, in two chunks of `exam_prep_cs301.txt` — "Final: everything from the midterm PLUS dynamic programming..." and "dynamic programming appears every year on the final. It is essentially guaranteed." Neither chunk is split across a boundary. **Yet neither ranks in the top 5.** The actual top results for this query are Chen's grade-distribution entry (dist 0.921), a Reddit post about exam regrade requests (0.925), and the exam-prep file's *header* chunk (1.003) — none of which name a topic.

The query "What topic appears on every final exam in Professor Chen's course?" contains no term that distinguishes the DP chunk; its strongest signals are "final exam" and "Chen's course," which match generic course-overview and exam-logistics chunks more closely than the specific chunk, whose decisive phrase "dynamic programming" never appears in the question. The generator never saw the DP statement and — correctly, per its grounding rules — declined to assert it.

This is a **retrieval-ranking / vocabulary-mismatch failure**, not a chunk-boundary or generation failure: the answer-bearing chunk shares few surface terms with a question that asks "which topic?" without naming the topic, so the embedding model buried it below broader, lexically-closer chunks. (My first hypothesis was a chunk-boundary split; inspecting the actual chunks disproved that — both DP chunks are whole — which is itself a lesson in verifying the failure mode instead of assuming it.) Likely fixes are retrieval-side: raise `top_k` to ~8 so the DP chunk enters the window, add query expansion, or use a hybrid keyword + semantic retriever so a rare-but-decisive term can be matched.

---

## 12. Spec reflection

- **Where planning.md helped:** the evaluation questions in §5 were specific enough (named professor + checkable fact) to catch a *real* retrieval failure. Q5 ("dynamic programming on every final") had a precise expected answer, so when the system couldn't surface it, the failure was unambiguous rather than a vague "the answer seemed a bit off." Concrete expected answers turned evaluation into a real test instead of a vibe check.
- **One divergence:** I originally planned `chunk_size=300`, but after running `inspect_chunks()` on the first build I saw that 300-character chunks were cutting reviews mid-sentence too often — a verdict would land in one chunk and its reasoning in the next. I increased to **400**, which let most single reviews stay whole, and the retrieval quality on Q1–Q3 improved noticeably.

---

## 13. AI usage

Claude was used as a pair programmer, with `planning.md` sections handed in as the spec for each component. Two specific instances:

- **`chunk_documents()`** — I gave Claude the "Chunking Strategy" section and asked it to implement the chunker. Its first draft used `CharacterTextSplitter`; I overrode that in favor of **`RecursiveCharacterTextSplitter`**, because the recursive version respects paragraph and sentence boundaries before doing a hard character cut, which keeps individual student reviews intact instead of slicing them arbitrarily.
- **`retrieve.py`** — I gave Claude the "Retrieval Approach" section and the architecture diagram and asked for the retrieval module. The generated code returned ChromaDB distances and sorted on them directly; in testing the distances came back as strings in one path, which made the sort non-numeric. I fixed it by **casting each distance to `float`** before sorting, so "most relevant first" ordering is always correct.

---

## How to run

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Groq API key
cp .env.example .env             # then edit .env and paste your key
# Get a free key at https://console.groq.com

# 4. Build the index (run once)
python scripts/build_index.py

# 5. Launch the app
python app.py                    # open http://localhost:7860
```
