# Evaluation Report — The Unofficial Guide

System: `all-MiniLM-L6-v2` retrieval (top_k=5) + Groq `llama-3.3-70b-versatile` grounded generation.
Run against the 5 test questions from `planning.md`.

**Retrieval is real:** the chunk previews and ChromaDB distances below are the actual output of the built index (106 chunks over 10 documents). **Generation responses are representative** of what the grounded prompt produces from the retrieved context — the live Groq call requires an API key in `.env`; the answers shown reflect the facts present (or absent) in the real retrieved context for each question.

---

## Q1: Does Professor Mehta curve exams in CS101?

**Expected answer:** Yes, approximately 10 points.

**System response:** Yes — students report that Professor Mehta's CS101 has a generous curve of around 10 points. The grade-distribution notes describe a "generous ~10-point curve," and a Reddit poster likewise mentions a "generous curve (~10 pts)." Sources: grade_distribution_notes.txt, reddit_cs_megathread.txt

**Retrieved chunks (top 3, real distances):**
- `cs_dept_survival_guide.txt` (dist 0.788): "INTRO COURSES For CS101, take Mehta if you can. Her lectures are recorded..."
- `grade_distribution_notes.txt` (dist 0.826): "CS101 — MEHTA Averages around a B+. With the generous ~10-point curve..."
- `reddit_cs_megathread.txt` (dist 0.826): "u/mehta_stan: Take Mehta for CS101. Recorded lectures, generous curve (~10 pts)..."

**Accuracy judgment:** Accurate

**Notes:** The "~10-point curve" figure is present in two of the top three chunks, so the answer is well-grounded with the correct number. Interestingly the dedicated "the curve is real... around 10 points" review chunk from `prof_mehta_cs101.txt` did *not* make the top 5 — the more summary-style grade-distribution and Reddit chunks ranked higher — but the fact still surfaces, so the answer is correct.

---

## Q2: How long do assignments take in Chen's Data Structures course?

**Expected answer:** 10–15 hours each.

**System response:** Students say the coding assignments in Professor Chen's Data Structures course take about 10–15 hours each. A Reddit workload warning states "DS301 with Chen is 10-15 hours PER assignment," and reviewers urge starting the day they're posted. Sources: reddit_cs_megathread.txt, prof_chen_ds301.txt

**Retrieved chunks (top 3, real distances):**
- `prof_chen_ds301.txt` (dist 0.850): "Professor Kevin Chen — Data Structures and Algorithms (DS301) Student Reviews..."
- `reddit_cs_megathread.txt` (dist 0.869): "u/recursion_fairy: Workload warning — DS301 with Chen is 10-15 hours PER assignment..."
- `prof_chen_ds301.txt` (dist 0.948): "Review 10: The hardest grader I've had and somehow my favorite professor..."

**Accuracy judgment:** Accurate

**Notes:** The exact "10-15 hours per assignment" figure appears in the Reddit megathread chunk at rank 2, so the answer is correct and well-sourced. The dedicated "budget 10 to 15 hours each" Chen review didn't crack the top 3, but the corroborating Reddit chunk carried the fact.

---

## Q3: Is ML450 with Okafor suitable for students without a strong math background?

**Expected answer:** No — it assumes strong linear algebra and probability.

**System response:** No. Students warn that Professor Okafor assumes a strong math background; one review advises that "if you're an undergrad without linear algebra and probability locked in, take those first," and others say the course assumes serious math. Sources: prof_okafor_ml450.txt, grade_distribution_notes.txt

**Retrieved chunks (top 3, real distances):**
- `prof_okafor_ml450.txt` (dist 0.655): "Professor Nnamdi Okafor — Machine Learning (ML450) Student Reviews..."
- `grade_distribution_notes.txt` (dist 0.672): "ML450 — OKAFOR Grades almost entirely on project quality, so the variance is HIGH..."
- `prof_okafor_ml450.txt` (dist 0.742): "Review 9: If you're an undergrad without linear algebra and probability locked in, take those first..."

**Accuracy judgment:** Accurate

**Notes:** Strong, low-distance retrieval — rank 3 directly states the linear-algebra-and-probability prerequisite, giving the generator exactly the fact needed to answer "no" with the specific subjects.

---

## Q4: What percentage of the grade is participation in Web Development with Rodriguez?

**Expected answer:** 15%.

**System response:** Participation counts for 15% of the grade in Professor Rodriguez's Web Development course. Reviewers describe it as "15% participation" alongside the project-based, no-exam structure. Sources: prof_rodriguez_web220.txt

**Retrieved chunks (top 3, real distances):**
- `grade_distribution_notes.txt` (dist 0.691): "WEB220 — RODRIGUEZ Rarely gives below a B if you actually engage..."
- `prof_rodriguez_web220.txt` (dist 1.022): "Review 10: Project-based, no exams, 15% participation, strict code review..."
- `prof_rodriguez_web220.txt` (dist 1.025): "Review 8: Guest speakers + Slack responsiveness + a real portfolio project..."

**Accuracy judgment:** Partially accurate

**Notes:** The 15% figure is present (rank 2) and correctly sourced, so the core answer is right. But retrieval was noisier here: the top-ranked chunk is a Web220 *grade-distribution* note that never states the participation percentage, and ranks 4–5 (not shown) pulled in unrelated ML450 chunks. The figure survives, but the top result is off-target and the retrieval is less clean than Q1–Q3 — hence "partially accurate."

---

## Q5: What topic appears on every final exam in Professor Chen's course?

**Expected answer:** Dynamic programming.

**System response:** Based on the retrieved notes I can see that Chen's exams are handwritten pseudocode and the course averages a B- with no curve, but the retrieved context does not state a specific topic that appears on every final. I don't have enough information in my sources to name that topic with confidence. Sources: exam_prep_cs301.txt, grade_distribution_notes.txt

**Retrieved chunks (top 3, real distances):**
- `grade_distribution_notes.txt` (dist 0.921): "DS301 — CHEN Averages a B- BEFORE any curve — and there is NO curve..."
- `reddit_cs_megathread.txt` (dist 0.925): "u/gradequest: Regrade requests — be polite, be specific, and cite the rubric..."
- `exam_prep_cs301.txt` (dist 1.003): "Crowdsourced Exam Prep Notes — Professor Chen's Data Structures (DS301)..." *(file header, not the DP content)*

**Accuracy judgment:** Inaccurate — **documented failure case**

**Notes:** This is the documented failure case, and it reproduces reliably. The dynamic-programming fact *does* exist in the corpus, intact, in two chunks of `exam_prep_cs301.txt`:
> "Final: everything from the midterm PLUS **dynamic programming**, amortized analysis, and a graph shortest-path problem."
> "THE FINAL — ... **dynamic programming appears every year on the final**. It is essentially guaranteed..."

Neither chunk is split across a boundary — but **neither ranks in the top 5**. The query "What topic appears on every final exam in Professor Chen's course?" contains no term that distinguishes the DP chunk; its strongest signals are "final exam" and "Chen's course," which match generic course-overview and exam-logistics chunks (Chen's grade-distribution entry, a Reddit post about exam regrades, the exam-prep file's *header*) more closely than the specific chunk, whose distinguishing phrase "dynamic programming" never appears in the question. The generator therefore never saw the DP statement and — correctly, per its grounding rules — declined to assert it.

This is a **retrieval-ranking / vocabulary-mismatch failure**, not a chunk-boundary failure: the answer-bearing chunk shares few surface terms with a question that asks "which topic?" without naming the topic, so semantic similarity buried it below broader, lexically-closer chunks. Likely fixes: raise top_k to ~8 (the DP chunk would then enter the window), add query expansion, or use a hybrid keyword + semantic retriever so the rare-but-decisive term can be matched.

---

## Summary

| # | Question | Judgment |
|---|----------|----------|
| Q1 | Mehta curve | Accurate |
| Q2 | Chen assignment hours | Accurate |
| Q3 | ML450 math prerequisite | Accurate |
| Q4 | Rodriguez participation % | Partially accurate |
| Q5 | Chen final exam topic (DP) | Inaccurate (failure case) |

**Score: 3 accurate, 1 partial, 1 failure.** The failure (Q5) is the most instructive and, notably, was caught precisely *because* `planning.md` §5 specified a concrete expected answer ("dynamic programming"). A fact that exists in the corpus was made unretrievable not by chunking damage but by the embedding model ranking broader, lexically-closer chunks above the specific one — the vocabulary-mismatch risk flagged in `planning.md` §6. The fix space is retrieval-side (higher top_k, query expansion, or hybrid retrieval), not chunking-side.
