# AINewsAgentic — LangGraph-Powered AI News & Chatbot Agent

## Overview

AINewsAgentic is an agentic AI application built on **LangGraph** that exposes
three use cases through a single Streamlit interface:

1. A **basic chatbot** powered by a Groq-hosted LLM.
2. A **chatbot with web search** that decides when to call the Tavily search
   tool and when to answer from its own knowledge.
3. An **AI News summarizer** that pulls daily / weekly / monthly AI-related
   news through Tavily and produces a dated, source-linked Markdown digest.

The application also includes a batch evaluation harness that runs every
(model × prompt × use case) combination, logs every response (with latency,
token usage, and tool-routing metadata), and produces summary tables across
five Groq models.

This is the final project for **CSC 7644: Applied LLM Development**.

---

## Key Features

- LangGraph state graph with three composable use cases (basic chat,
  tool-augmented chat, news pipeline).
- Tool-augmented agent that uses `tools_condition` to route between the LLM
  and a Tavily web-search tool.
- News pipeline with three explicit nodes — `fetch_news → summarize_news →
  save_result` — that writes Markdown digests into `AINews/`.
- Streamlit UI with model selector (5 Groq models), use-case selector, and a
  status-aware chat-input border (idle / processing / error).
- Response logger that writes every interaction to `evaluations/<usecase>/
  <model>/<subcategory>/<timestamp>.md` with YAML frontmatter capturing
  latency, token usage, tool calls, and routing correctness.
- Batch evaluation runner (`batch_run.py`) and aggregation script
  (`evaluate.py`) that produce per-model summary tables and a CSV roll-up.

---

## Tech Stack

| Layer            | Tooling                                              |
|------------------|------------------------------------------------------|
| LLM provider     | [Groq](https://groq.com) (Llama-3.x, GPT-OSS, Qwen)  |
| Agent framework  | [LangGraph](https://github.com/langchain-ai/langgraph) + LangChain |
| Web search tool  | [Tavily](https://tavily.com)                         |
| UI               | [Streamlit](https://streamlit.io)                    |
| Config / secrets | `python-dotenv`, `configparser`                      |

### High-Level Architecture

```
Streamlit UI (loadui.py, display_result.py)
        │
        ▼
GroqLLM  ──►  GraphBuilder  ──►  StateGraph (LangGraph)
                                     │
            ┌────────────────────────┼────────────────────────┐
            ▼                        ▼                        ▼
   Basic Chatbot Node       Chatbot+Tool Node          AI News Nodes
   (single LLM call)      (LLM ⇄ Tavily ToolNode)   (fetch → summarize → save)
                                                            │
                                                            ▼
                                                    AINews/*.md digests
        │
        ▼
ResponseLogger  ──►  evaluations/<usecase>/<model>/<timestamp>.md
```

---

## Repository Organization

```
AINEWSAgentic/
├── app.py                      # Streamlit entrypoint (calls main.load_langgraph_agenticai_app)
├── batch_run.py                # Runs every model × prompt × use case combo
├── evaluate.py                 # Aggregates evaluations/ into summary tables + CSV
├── requirements.txt
├── .env.example                # Template — copy to .env and fill in keys
├── AINews/                     # Generated AI-news digests (daily/weekly/monthly)
├── evaluations/                # Per-run logs written by ResponseLogger (gitignored)
├── EVALUATION_REPORT.md        # Written-up findings from the batch runs
├── evaluation_summary.csv      # Aggregated metrics produced by evaluate.py
└── src/
    └── langgraphagenticai/
        ├── main.py             # Streamlit app loop and status-border styling
        ├── LLMS/groqllm.py     # Groq model factory
        ├── graph/graph_builder.py      # Builds one of three LangGraph graphs
        ├── nodes/
        │   ├── basic_chatbot_node.py
        │   ├── chatbot_with_Tool_node.py
        │   └── ai_news_node.py         # fetch_news / summarize_news / save_result
        ├── tools/search_tool.py        # Tavily search tool + ToolNode factory
        ├── state/state.py              # TypedDict graph state
        ├── ui/
        │   ├── uiconfigfile.ini        # Page title, model list, use-case list
        │   ├── uiconfigfile.py
        │   └── streamlitui/            # loadui.py, display_result.py
        └── evaluation/logger.py        # ResponseLogger + token-usage extractor
```

---

## Setup Instructions

### Prerequisites

- **Python 3.10+** (tested on Linux / Ubuntu).
- `pip` (a `venv` or `conda` environment is strongly recommended).
- API keys for:
  - **Groq** — sign up at <https://console.groq.com> and create a key.
  - **Tavily** — sign up at <https://app.tavily.com> and create a key.

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd AINEWSAgentic
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate          # on Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in your own keys — **never commit `.env`**.

```bash
cp .env.example .env
```

`.env` must contain:

```
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
```

Both keys are required:

| Variable          | Used by                                                  |
|-------------------|----------------------------------------------------------|
| `GROQ_API_KEY`    | `GroqLLM` for every use case                             |
| `TAVILY_API_KEY`  | `TavilySearchResults` (web tool) and `AINewsNode`        |

---

## Running the Application

### Streamlit UI (primary entry point)

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically <http://localhost:8501>).

In the sidebar:

1. Select **Groq** as the LLM provider and pick a model
   (e.g. `llama-3.3-70b-versatile`).
2. Choose a use case — `Basic Chatbot`, `Chatbot With Web`, or `AI News`.
3. For **AI News**, choose a frequency (Daily / Weekly / Monthly) and click
   the fetch button. The summary is written to `AINews/<frequency>_summary.md`.
4. For chat use cases, type into the chat input. The border turns yellow
   while the LLM is thinking and red on error.

### Batch evaluation run

`batch_run.py` exercises every model on every prompt/use case and writes one
log file per response.

```bash
python batch_run.py
```

### Aggregating evaluations

`evaluate.py` walks `evaluations/`, prints per-model summary tables (mean
latency, tokens, error count, tool-routing accuracy, AI-news latency vs.
target), and writes `evaluation_summary.csv`.

```bash
python evaluate.py
```

The narrative report based on those numbers lives in
[EVALUATION_REPORT.md](EVALUATION_REPORT.md).

---

## Configuring Available Models / Use Cases

The model dropdown, use-case list, and page title are driven by
[`src/langgraphagenticai/ui/uiconfigfile.ini`](src/langgraphagenticai/ui/uiconfigfile.ini).
Add or remove entries there to expose new models or use cases in the UI.

---

## Security Notes

- `.env` is listed in `.gitignore` and **must never be committed**. Use
  `.env.example` (with empty placeholder values) as the only template that
  ships with the repo.
- `evaluations/` is also gitignored to avoid leaking prompt/response content.
- If a key is ever accidentally pushed, **revoke it immediately** in the
  Groq / Tavily console and rotate.

---

## Attributions and Citations

- LangGraph and LangChain documentation and examples:
  <https://langchain-ai.github.io/langgraph/> ,
  <https://python.langchain.com/>
- Groq Python integration via `langchain-groq`:
  <https://python.langchain.com/docs/integrations/chat/groq/>
- Tavily search integration:
  <https://docs.tavily.com/> and
  `langchain_community.tools.tavily_search.TavilySearchResults`
- Streamlit chat UI patterns:
  <https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps>
- The overall LangGraph "build stateful agentic AI graph" scaffold (UI
  loader, graph builder, node split) was adapted from publicly available
  LangGraph tutorial material and then extended with the AI News pipeline,
  status-aware Streamlit styling, the `ResponseLogger`, and the
  batch-evaluation / aggregation scripts written for this project.

All other code in this repository was written by the author for CSC 7644.
