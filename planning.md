# Planning — The Unofficial Guide

*Written before implementation. This is the design I committed to before writing any pipeline code.*

---

## 1. Domain

My system covers **student-generated knowledge about CS professors and courses** — the candid, experience-based information students actually trade on Rate My Professors, Reddit, and class Discord/Slack servers. Things like: which professor curves, how many hours an assignment really takes, whether "open-note" actually means "easy," and which TA to go see when you're stuck.

This knowledge is valuable because it's *decision-grade*: it's what students use to pick courses, plan a manageable semester, and avoid landmines like stacking two 20-hour-a-week classes together. It's also **hard to find through official channels**:

- **Academic advisors give diplomatic non-answers.** They won't tell you a professor is a brutal grader; they'll say "it's a rigorous course."
- **Professor websites and bios are promotional.** They describe research, not exam time-pressure or autograder bugs.
- **Official syllabi don't capture the lived experience.** A syllabus lists topics and grade weights but never says "start the kernel assignment the day it drops or you'll take a zero."

The official sources describe the course on paper; this corpus describes what taking it actually feels like.

---

## 2. Documents

Ten student-written `.txt` files in `data/raw/`:

1. **prof_mehta_cs101.txt** — Student reviews of Prof. Mehta's intro CS course (recorded lectures, generous curve, time-pressured exams, autograder bugs, research-talk extra credit).
2. **prof_chen_ds301.txt** — Reviews of Prof. Chen's Data Structures course (hard grader, no curve, 10–15 hour assignments, handwritten pseudocode exams, generous partial credit).
3. **prof_okafor_ml450.txt** — Reviews of Prof. Okafor's Machine Learning course (research-focused, strong-math prerequisite, 70% project grade, team projects, paper readings).
4. **prof_rodriguez_web220.txt** — Reviews of Prof. Rodriguez's Web Development course (project-based, React/Node/PostgreSQL, 15% participation, strict code review, responsive on Slack).
5. **prof_kim_os410.txt** — Reviews of Prof. Kim's Operating Systems course (hardest CS course, 20+ hour kernel assignments, open-note exams, live coding, strict prereq).
6. **cs_dept_survival_guide.txt** — An unofficial student-written department survival guide (registration lottery, closed sections, helpful TAs, course sequencing, pitfalls).
7. **reddit_cs_megathread.txt** — Compiled excerpts from a "what I wish I knew" subreddit megathread (workload warnings, regrade tips, recruiting timeline, honor-code advice).
8. **prof_mehta_office_hours_tips.txt** — Targeted tips for getting the most out of Mehta's office hours and CS101 (timing, Socratic method, TA Marcus, Friday sessions).
9. **exam_prep_cs301.txt** — Crowdsourced exam-prep notes for Chen's Data Structures (frequent midterm topics, heap/hash-table mistakes, how Chen grades pseudocode, DP on every final).
10. **grade_distribution_notes.txt** — Informal student observations on grade distributions across the five courses (averages, OS410's D/F rate, pass/fail and late-drop advice).

---

## 3. Chunking Strategy

**`chunk_size = 400` characters, `chunk_overlap = 80` characters**, using LangChain's `RecursiveCharacterTextSplitter`.

The reasoning is corpus-specific. Almost every document is a list of **short opinion units** — a single student review or a single piece of advice — and each unit is typically **2–5 sentences**. 400 characters is roughly that length, so a 400-char chunk tends to capture **one complete thought about one professor**: the claim plus its justification ("no curve, but partial credit is generous, so write something").

The **80-char overlap** exists to keep a review's *rating* attached to its *explanation* when a boundary lands in the middle of one. Without overlap, a chunk could end on "the curve is generous —" and the next chunk start with "around 10 points," splitting the actual number away from the claim it answers.

What bad retrieval looks like at the wrong sizes:

- **Too small (e.g. 100 chars):** chunks become fragments with no context — "Start early." Start *what* early? The retriever can match the words but the chunk can't actually answer the question because the subject got severed.
- **Too large (e.g. 1500 chars):** a single chunk merges multiple reviews and sometimes multiple professors. A query about Mehta's exams might pull a chunk that's 70% about Chen, **diluting the specificity** of the embedding and the answer.

400/80 is the size where one chunk ≈ one self-contained student opinion.

---

## 4. Retrieval Approach

**Embedding model: `all-MiniLM-L6-v2`** via `sentence-transformers`. Chosen because it is **local** (no API cost or network dependency for embeddings), **fast** (384-dim, runs fine on a laptop CPU), and **well-suited to short text** — it was trained heavily on sentence-level semantic similarity, which is exactly the shape of our chunks.

**`top_k = 5`.** Most questions are answerable from one or two reviews, but several documents discuss the same professor, so pulling 5 chunks gives the generator enough corroborating context to be confident while staying small enough to keep the prompt focused.

**Production tradeoffs a real system would weigh:**
- **Accuracy:** a hosted model like OpenAI `text-embedding-3-large` would likely retrieve more precisely, at the cost of per-query API calls and a network dependency.
- **Multilingual support:** for international students writing reviews in other languages, a multilingual embedding model (e.g. `paraphrase-multilingual-MiniLM`) would matter.
- **Cost at scale:** local MiniLM is free per query; a hosted embedding API bills per token on *every* query and every re-index, which adds up fast for a campus-wide deployment.

---

## 5. Evaluation Plan

Five test questions with specific, checkable expected answers:

| # | Question | Expected answer |
|---|----------|-----------------|
| Q1 | Does Professor Mehta curve exams in CS101? | Yes, approximately 10 points |
| Q2 | How long do assignments take in Chen's Data Structures course? | 10–15 hours each |
| Q3 | Is ML450 with Okafor suitable for students without a strong math background? | No — it assumes strong linear algebra and probability |
| Q4 | What percentage of the grade is participation in Web Development with Rodriguez? | 15% |
| Q5 | What topic appears on every final exam in Professor Chen's course? | Dynamic programming |

Each is graded **Accurate / Partially accurate / Inaccurate** based on whether the generated answer matches the expected fact *and* cites a correct source.

---

## 6. Anticipated Challenges

1. **Multi-professor documents cause off-topic retrieval.** Files like the survival guide, the Reddit megathread, and the grade-distribution notes mention several professors at once. A query about one professor may pull a chunk that name-drops them but is really about someone else.
2. **Slang and abbreviations may embed poorly.** Students write "OS," "ML," "DS" rather than "Operating Systems," "Machine Learning," "Data Structures." A query using the full name may not align well with a chunk using only the abbreviation (and vice versa).
3. **Chunk boundaries may split a rating from its explanation.** A review's verdict and the reason behind it can land on opposite sides of a 400-char boundary; the 80-char overlap mitigates this but won't catch every case.

---

## 7. AI Tool Plan

I plan to use Claude as a pair programmer, feeding it the relevant section of *this* planning doc as the spec for each component:

- **`ingest.py`** — give Claude the "Documents" section and ask for a loader + cleaner that normalizes the messy student text.
- **`chunk.py`** — give Claude the "Chunking Strategy" section verbatim so the 400/80 rationale and the splitter choice come straight from the plan.
- **`embed.py` / `retrieve.py`** — give Claude the "Retrieval Approach" section plus the architecture diagram so it wires MiniLM + ChromaDB consistently.
- **`generate.py`** — give Claude the exact system-prompt text and the grounding requirements.
- **`app.py`** — give Claude the UI layout spec for the Gradio interface.

I'll review every generation against the plan, correct anything that drifts (e.g. wrong splitter class, string-vs-float bugs), and keep the plan as the source of truth.

---

## 8. Architecture

```
Raw .txt files (data/raw/)
        │
        ▼
ingest.py            load + clean (normalize quotes, strip separators, collapse blanks)
        │
        ▼
chunk.py             RecursiveCharacterTextSplitter (chunk_size=400, overlap=80)
        │
        ▼
embed.py             all-MiniLM-L6-v2 embeddings  ──►  ChromaDB (persistent collection)
        │
        ▼
retrieve.py          semantic search (embed query, top-5 by distance)
        │
        ▼
generate.py          Groq llama-3.3-70b-versatile, grounded system prompt, temp=0.2
        │
        ▼
app.py               Gradio UI (question → answer + sources + debug chunks)
```
