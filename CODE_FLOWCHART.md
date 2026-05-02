# AINEWSAgentic — Code Flow Documentation

A complete visual guide to understanding the codebase: directory structure, runtime execution flow, and LangGraph pipelines.

---

## Directory Structure

```
Midterm project/AINEWSAgentic/
│
├── app.py ← ENTRY POINT (run this)
├── requirements.txt ← dependencies
├── .env ← API keys (GROQ_API_KEY, TAVILY_API_KEY)
├── .gitignore
├── README.md
│
├── AINews/ ← OUTPUT folder (markdown summaries)
│ ├── daily_summary.md
│ ├── weekly_summary.md
│ └── monthly_summary.md
│
└── src/langgraphagenticai/
 │
 ├── main.py ← orchestrator
 │
 ├── ui/
 │ ├── uiconfigfile.ini ← config: page title, models list, use cases
 │ ├── uiconfigfile.py ← Config class (reads .ini)
 │ └── streamlitui/
 │ ├── loadui.py ← LoadStreamlitUI (sidebar widgets)
 │ └── display_result.py ← DisplayResultStreamlit (renders output)
 │
 ├── LLMS/
 │ └── groqllm.py ← GroqLLM (initializes ChatGroq client)
 │
 ├── graph/
 │ └── graph_builder.py ← GraphBuilder (assembles LangGraph)
 │
 ├── nodes/ ← LangGraph nodes (the "agents")
 │ ├── basic_chatbot_node.py ← simple chat
 │ ├── chatbot_with_Tool_node.py ← chat + Tavily web search
 │ └── ai_news_node.py ← fetch → summarize → save (3-step graph)
 │
 ├── tools/
 │ └── search_tool.py ← Tavily wrapper for chatbot tool calls
 │
 └── state/
 └── state.py ← TypedDict shared between graph nodes
```

---

## Runtime Execution Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ USER runs: streamlit run app.py │
└────────────────────────────────┬─────────────────────────────────┘
 │
 ▼
┌──────────────────────────────────────────────────────────────────┐
│ app.py │
│ └─► load_langgraph_agenticai_app() │
└────────────────────────────────┬─────────────────────────────────┘
 │
 ▼
┌──────────────────────────────────────────────────────────────────┐
│ main.py — load_langgraph_agenticai_app() │
│ │
│ 1. ui = LoadStreamlitUI() ─► reads .ini + .env │
│ 2. user_input = ui.load_streamlit_ui() (sidebar widgets) │
│ 3. obj_llm_config = GroqLLM(user_input) │
│ 4. model = obj_llm_config.get_llm_model() ─► ChatGroq client │
│ 5. graph_builder = GraphBuilder(model) │
│ 6. graph = graph_builder.setup_graph(usecase) │
│ 7. DisplayResultStreamlit(usecase, graph, msg).display_…() │
└────────────────────────────────┬─────────────────────────────────┘
 │
 ▼
 ┌──────────────────────┐
 │ Which use case? │
 └──┬─────────┬─────────┴──┐
 │ │ │
 ┌──────────▼┐ ┌──────▼────────┐ ┌─▼──────────┐
 │Basic │ │Chatbot With │ │AI News │
 │Chatbot │ │Web │ │ │
 └──────────┬┘ └──────┬────────┘ └─┬──────────┘
 │ │ │
 ▼ ▼ ▼
 See LangGraph diagrams below ───────────
```

---

## LangGraph Pipelines (one per use case)

### 1. Basic Chatbot

```
 START ──► [chatbot] ──► END
 │
 └─► BasicChatbotNode.process()
 └─► llm.invoke(messages)
```

### 2. Chatbot With Web (tool-using agent)

```
 START ──► [chatbot] ──┬──► tools_condition? ──► END
 ▲ │
 │ ▼
 │ [tools] ◄─── TavilySearchResults (search_tool.py)
 │ │
 └────────┘ (loops until no tool call needed)
```

### 3. AI News (the 3-step pipeline)

```
 START ──► [fetch_news] ──► [summarize_news] ──► [save_result] ──► END
 │ │ │
 ▼ ▼ ▼
 TavilyClient.search() llm.invoke(prompt) write to
 topic="news" with article list AINews/{freq}_summary.md
 time_range=d/w/m
 max_results=20
```

---

## Data / State Flow (AI News use case)

```
sidebar selection: "Weekly"
 │
 ▼
state = {"messages": "Weekly"}
 │
 ▼
┌─────────────────┐
│ fetch_news │ ──► state['news_data'] = [article1, article2, ...]
└─────────────────┘ (list of dicts: content, url, published_date)
 │
 ▼
┌─────────────────┐
│ summarize_news │ ──► state['summary'] = "### 2026-04-22\n- [....]"
└─────────────────┘ (markdown string from LLM)
 │
 ▼
┌─────────────────┐
│ save_result │ ──► writes ./AINews/weekly_summary.md
└─────────────────┘
 │
 ▼
DisplayResultStreamlit reads the .md file and renders in browser
```

---

## Key Design Patterns

| Concept | Where | What it does |
|---|---|---|
| **Config** | `uiconfigfile.ini` + `uiconfigfile.py` | All UI options live in `.ini`; Python class parses it. Add a model? Just edit the `.ini`. |
| **State** | `state/state.py` | `TypedDict` with `messages` field — shared bus passed node→node |
| **Nodes** | `nodes/*.py` | Each is a class with a `process()` or step-method that takes `state` and returns updated `state` |
| **Graph** | `graph_builder.py` | Wires nodes together as a directed graph with `add_node` / `add_edge` |
| **Tools** | `tools/search_tool.py` | External capabilities the LLM can choose to call (Tavily web search) |
| **UI** | `streamlitui/loadui.py` + `display_result.py` | Input on the left, output rendering on the right |

---

## Mental Model

Think of it as a **router pattern**:

> One Streamlit app → one config-driven sidebar → routes to **one of three LangGraph pipelines** → renders results back to the user.

The "agentic" part is that pipeline 2 lets the LLM decide *whether* to call a tool, and pipeline 3 chains three sequential steps (fetch → summarize → save) into an autonomous workflow.

---

## How to Run

```bash
# 1. Activate the conda environment
conda activate csc7644

# 2. Install dependencies (first time only)
cd "/home/saiful/Applied_LLM_Development/Midterm project/AINEWSAgentic"
pip install -r requirements.txt

# 3. Run the Streamlit app
streamlit run app.py

# 4. Open the browser at:
# http://localhost:8501 (local)
# http://130.39.93.86:8501 (remote / server IP)
```

API keys are auto-loaded from `.env` — no need to enter them in the sidebar.

---

## API Keys Required

| Key | Used For | Get it at |
|---|---|---|
| `GROQ_API_KEY` | LLM inference (all use cases) | https://console.groq.com/keys |
| `TAVILY_API_KEY` | Web search & news fetching (Chatbot With Web, AI News) | https://app.tavily.com/home |

Both live in `.env` at the project root.

---

## Available Models (Groq)

Configured in `src/langgraphagenticai/ui/uiconfigfile.ini`:

1. **llama-3.3-70b-versatile** — best quality (Meta)
2. **llama-3.1-8b-instant** — fastest (Meta)
3. **openai/gpt-oss-120b** — large reasoning model (OpenAI)
4. **meta-llama/llama-4-scout-17b-16e-instruct** — newest Llama 4 (Meta)
5. **qwen/qwen3-32b** — strong open model (Alibaba)

> Note: `gpt-oss` models use a "reasoning" output format that can exhaust completion tokens on long prompts (e.g., the 20-article news summarizer). For the **AI News** use case, prefer `llama-3.3-70b-versatile`.

---

# Script-by-Script Walkthrough

A guided tour through every script in the codebase, in the recommended reading order (simple → complex).

## Recommended Reading Order

| # | Script | Why this order |
|---|---|---|
| 1 | `app.py` | Entry point — 4 lines, sets the stage |
| 2 | `ui/uiconfigfile.ini` + `ui/uiconfigfile.py` | Config layer — defines available options |
| 3 | `state/state.py` | Data shape passed between nodes |
| 4 | `LLMS/groqllm.py` | LLM client setup |
| 5 | `nodes/basic_chatbot_node.py` | Simplest agent (1 LLM call) |
| 6 | `tools/search_tool.py` | Tool definition (Tavily) |
| 7 | `nodes/chatbot_with_Tool_node.py` | Tool-using agent |
| 8 | `nodes/ai_news_node.py` | Most complex node (3 steps) |
| 9 | `graph/graph_builder.py` | Wires nodes into LangGraph |
| 10 | `ui/streamlitui/loadui.py` | Sidebar UI |
| 11 | `ui/streamlitui/display_result.py` | Output rendering |
| 12 | `main.py` | Orchestrator — ties everything together |

---

## Script 1 of 12 — `app.py`

**File:** `app.py`

```python
from src.langgraphagenticai.main import load_langgraph_agenticai_app

if __name__=="__main__":
 load_langgraph_agenticai_app()
```

### What it does

This is the **launcher**. When you run `streamlit run app.py`, Streamlit executes this file top to bottom.

### Line-by-line

| Line | Purpose |
|---|---|
| `from src.langgraphagenticai.main import load_langgraph_agenticai_app` | Imports the main function from `src/langgraphagenticai/main.py` |
| `if __name__=="__main__":` | Standard Python guard — ensures code only runs when this file is the entry point |
| `load_langgraph_agenticai_app()` | Calls the orchestrator function (which you'll see in script #12) |

### Why this design?

The author kept `app.py` deliberately **thin** — it does nothing but delegate. This is a common pattern:

- `app.py` = launcher (Streamlit's required entry)
- `main.py` = the real logic

Benefits:

- Easy to swap the entry point later (e.g., wrap in FastAPI, CLI, etc.)
- Keeps the project root clean
- The actual app logic lives inside the `src/` package, which is more testable and importable

### Key takeaway

Whenever you see a tiny `app.py`, immediately jump to whatever it imports — that's where the real story begins. In our case, that's `main.py` (which we'll read last, after understanding all its dependencies).

