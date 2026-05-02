# Evaluation Report — Cross-Model Performance

**Date:** 2026-05-01
**Reviewer:** Human spot-check on logged outputs in `evaluations/`
**Scope:** 5 models × 3 use cases × 80 logged runs

---

## 1. Functional Completeness

| Model | Basic Chatbot | Chatbot With Web | AI News | Verdict |
|---|---|---|---|---|
| llama-3.3-70b-versatile | 5/5 | 10/10 | 1/1 | Full |
| llama-3.1-8b-instant | 5/5 | 8/10 (2 tool_use_failed) | 1/1 | Partial |
| openai/gpt-oss-120b | 5/5 | 8/10 (rate-limit + 413) | 1/1 | Partial |
| meta-llama/llama-4-scout | 5/5 | 10/10 | 1/1 | Full |
| qwen/qwen3-32b | 5/5 | 9/10 (1 rate-limit) | 0/1 (413) | AI News fails |

**Conclusion:** Only the two Llama models with the largest production footprint (3.3-70b and 4-scout) survived all three pipelines cleanly. `qwen3-32b` cannot complete AI News because the 20-article prompt exceeds the **6 000-TPM free-tier limit**. `gpt-oss-120b` hit token-per-minute caps mid-batch.

---

## 2. Output Quality (manual spot-check)

### 2a. Critical finding — "What is RAG?" prompt

This single prompt is the most discriminating in the test set:

| Model | Answer | Reviewer note |
|---|---|---|
| llama-3.1-8b-instant | "Red, Amber, Green" | **Wrong domain** — interpreted as project-management acronym |
| llama-3.3-70b-versatile | "Red, Amber, Green" | **Wrong domain** — same hallucination as the small Llama |
| meta-llama/llama-4-scout | "Retrieval-Augmented Generation" + accurate explanation | Correct |
| openai/gpt-oss-120b | "Retrieval-Augmented Generation" + comparison table + workflow diagram | Best answer, well-formatted |
| qwen/qwen3-32b | Correct, but emits a giant `<think>...</think>` reasoning block in the visible response | Correct content, broken UX |

**Reviewer assessment:** The Llama family appears to default to the project-management meaning of "RAG" — a striking failure given the obvious AI/ML context (Streamlit page titled "LangGraph: Build Stateful Agentic AI graph"). For a deployment that targets developers, this is a **production-blocker** issue with both Llama 3.x models.

### 2b. AI News summary quality

Compared the same 20 source articles across 4 models that completed the run:

| Model | Format | Detail level | Reviewer score (Acc/Comp/Fmt) |
|---|---|---|---|
| llama-3.3-70b-versatile | Markdown, headlines as links | Just titles — **no summary sentences** despite the system-prompt instruction "Concise sentences summary" | 4 / 2 / 4 |
| llama-3.1-8b-instant | `### **Date**` (bold inside heading — non-standard) | Same problem: titles only, no sentences | 4 / 2 / 3 |
| openai/gpt-oss-120b | Markdown with bold highlights, em-dashes | **Excellent** — specific numbers ("$100M for Fury"), concrete facts ("plans H2-2026 listing"), expanded context | 5 / 5 / 5 |
| meta-llama/llama-4-scout | Markdown with parenthetical source labels | **Strong** — actually summarizes each article in 1-2 sentences, marks "No articles" for empty dates | 5 / 5 / 5 |

**Reviewer assessment:** The two Llama models *failed to follow the system prompt*. The prompt explicitly asked for "concise sentences summary from latest news," but they produced a list of titles with hyperlinks. **gpt-oss-120b** and **llama-4-scout** are the only models that delivered what the spec asked for. Of those two, gpt-oss is more detailed; scout is faster.

---

## 3. Latency & Cost

### Latency (mean seconds per call)

| Model | Basic Chatbot | Chatbot With Web | AI News (Weekly) |
|---|---|---|---|
| llama-3.3-70b-versatile | 1.3 | 2.4 | 3.2 |
| llama-3.1-8b-instant | 0.9 | 9.9 | 2.3 |
| openai/gpt-oss-120b | 2.1 | 21.4 (rate-limited spikes) | 6.9 |
| meta-llama/llama-4-scout | 1.1 | 1.9 | **2.1** ⭐ fastest |
| qwen/qwen3-32b | 3.3 | 13.0 | n/a (failed) |

### vs Original targets (AI News)

- Daily ≤ 30s: all 4 successful models pass with huge margin (≤7s)
- Weekly ≤ 45s: all 4 pass
- Monthly ≤ 60s: not tested (would only matter if the month spans more articles)

### Cost estimate

Total tokens consumed across 80 runs ≈ **~120,000 tokens**. At Groq's free-tier pricing (no charge under TPM limits), actual cost is **$0.00**. Even at on-demand rates ($0.05–$0.79/M tokens), worst-case spend is **~$0.10**. Free-tier compliance is verified.

---

## 4. Tool Orchestration (Chatbot With Web)

### Routing accuracy on the 10-prompt test (5 trigger + 5 no-trigger)

| Model | Correct routes | Accuracy |
|---|---|---|
| meta-llama/llama-4-scout | 10/10 | **100%** ⭐ |
| openai/gpt-oss-120b | 8/8 (2 lost to rate-limit, not routing) | **100%** ⭐ |
| qwen/qwen3-32b | 9/9 | **100%** ⭐ |
| llama-3.3-70b-versatile | 9/10 | 90% |
| llama-3.1-8b-instant | 5/8 | **62.5%** |

**Reviewer assessment:** The smaller Llama (8B) is **over-eager to call tools**. It triggered Tavily search for trivial prompts like:
- "Explain how recursion works."
- "Translate 'good morning' to French."
- "Define photosynthesis in one sentence."

These are textbook knowledge questions; calling a search tool wastes latency and tokens. The 70B variant only mis-routed once. The other three families (scout, gpt-oss, qwen) showed perfect judgment.

---

## 5. Reviewer's Final Recommendation

### First place: **`meta-llama/llama-4-scout-17b-16e-instruct`**
- Answered RAG correctly
- Followed AI News prompt (real summaries)
- Fastest AI News pipeline (2.1s)
- 100% tool routing
- **No errors anywhere**

### Second: **`openai/gpt-oss-120b`** (best when not rate-limited)
- Best output quality overall (richest summaries, best formatting)
- 100% tool routing
- Slowed down by free-tier TPM caps; would shine on a paid tier
- Recommended only if you upgrade past free tier

### Third: **`llama-3.3-70b-versatile`**
- Reliable and fast
- Great for chat-only tasks
- Disappointing on RAG (factual error) and AI News (no summaries — just links)

### Not recommended for this project
- **`llama-3.1-8b-instant`** — over-eager tool routing (62.5%), tool_use_failed errors, also got RAG wrong
- **`qwen/qwen3-32b`** — leaks `<think>` blocks into output, can't fit AI News in free-tier TPM

---

## 6. Notes on the evaluation infrastructure

- **`batch_run.py`** automated 80 calls in ~12 min with rate-limit padding
- **`evaluate.py`** parses YAML frontmatter and produces summary tables + CSV
- **`scoring_template.md`** — for manual quality scoring
- **`evaluation_prompts.md`** — the canonical prompt sheet for reproducibility
- All raw responses live in `evaluations/{usecase}/{model}/[subcategory]/{ts}.md`
- `evaluation_summary.csv` is machine-readable for further analysis

### Bug found and fixed during this evaluation

- **Issue:** `news_data` and `summary` were not flowing through `graph.invoke()` results.
- **Cause:** `State` TypedDict only declared `messages`; LangGraph dropped undeclared keys.
- **Fix:** Added `news_data`, `summary`, `usage_metadata`, `filename` as `NotRequired` fields in [state.py](src/langgraphagenticai/state/state.py).
- **Impact:** Original streamlit display happened to work for some models because the file was written by `save_result` (which the streamlit code re-reads). The AI News evaluation logger needed the in-memory state, which the fix now provides.
