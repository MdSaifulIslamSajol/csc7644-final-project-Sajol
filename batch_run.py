"""Batch evaluation runner.

Runs every (model × prompt × use case) combination, saves each response via the
existing ResponseLogger so outputs land in `evaluations/` exactly like manual
runs do.
"""
import os
import sys
import time
import traceback
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.langgraphagenticai.LLMS.groqllm import GroqLLM
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from src.langgraphagenticai.evaluation.logger import ResponseLogger, extract_token_usage


MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
]

BASIC_CHATBOT_PROMPTS = [
    "Explain attention mechanism in transformers in 3 sentences.",
    "What is RAG and why is it used?",
    "Compare supervised vs unsupervised learning.",
    "Write Python code to reverse a string.",
    "Summarize the difference between AI, ML, and DL.",
]

WEB_PROMPTS_TRIGGER = [
    "What are the latest AI news from this week?",
    "What did OpenAI announce most recently?",
    "What is today's NVIDIA stock price?",
    "Who won the 2025 Turing Award?",
    "What's the latest stable version of Python?",
]

WEB_PROMPTS_NO_TRIGGER = [
    "Explain how recursion works.",
    "Write a haiku about programming.",
    "What is 17 times 23?",
    "Translate 'good morning' to French.",
    "Define photosynthesis in one sentence.",
]

AI_NEWS_FREQUENCIES = ["Weekly"]  # subset to keep runtime + Tavily quota in check


def make_llm(model_name):
    cfg = {"GROQ_API_KEY": os.environ["GROQ_API_KEY"], "selected_groq_model": model_name}
    return GroqLLM(user_contols_input=cfg).get_llm_model()


def run_basic_chatbot(model_name, prompt, llm):
    logger = ResponseLogger("Basic Chatbot", model_name)
    graph = GraphBuilder(llm).setup_graph("Basic Chatbot")
    start = time.time()
    try:
        result = graph.invoke({"messages": [("user", prompt)]})
        elapsed = time.time() - start
        msgs = result.get("messages", [])
        ai = next((m for m in reversed(msgs) if isinstance(m, AIMessage)), None) if isinstance(msgs, list) else msgs
        text = ai.content if ai is not None else ""
        tokens = extract_token_usage(ai) if ai is not None else {}
        path = logger.save(query=prompt, response=text, latency_seconds=elapsed, **tokens)
        return {"ok": True, "path": path, "latency": elapsed, "tokens": tokens.get("total_tokens"), "preview": text[:80]}
    except Exception as e:
        elapsed = time.time() - start
        path = logger.save(query=prompt, response=f"ERROR: {e}", latency_seconds=elapsed, error=str(e)[:300])
        return {"ok": False, "path": path, "latency": elapsed, "error": str(e)[:200]}


def run_chatbot_with_web(model_name, prompt, expected_tool, llm):
    logger = ResponseLogger("Chatbot With Web", model_name)
    graph = GraphBuilder(llm).setup_graph("Chatbot With Web")
    start = time.time()
    try:
        result = graph.invoke({"messages": [prompt]})
        elapsed = time.time() - start
        msgs = result.get("messages", [])
        tool_calls = [m for m in msgs if isinstance(m, ToolMessage)]
        ai = next((m for m in reversed(msgs) if isinstance(m, AIMessage) and m.content), None)
        text = ai.content if ai else ""
        tool_used = len(tool_calls) > 0
        subcat = "with_tool" if tool_used else "no_tool"
        tokens = extract_token_usage(ai) if ai else {}
        path = logger.save(
            query=prompt,
            response=text,
            latency_seconds=elapsed,
            subcategory=subcat,
            tool_used=tool_used,
            tool_call_count=len(tool_calls),
            expected_tool=expected_tool,
            routing_correct=(tool_used == expected_tool),
            **tokens,
        )
        return {"ok": True, "path": path, "latency": elapsed, "tool_used": tool_used,
                "expected": expected_tool, "correct": tool_used == expected_tool, "preview": text[:80]}
    except Exception as e:
        elapsed = time.time() - start
        path = logger.save(query=prompt, response=f"ERROR: {e}", latency_seconds=elapsed,
                           subcategory="error", error=str(e)[:300])
        return {"ok": False, "path": path, "latency": elapsed, "error": str(e)[:200]}


def run_ai_news(model_name, frequency, llm):
    logger = ResponseLogger("AI News", model_name)
    graph = GraphBuilder(llm).setup_graph("AI News")
    start = time.time()
    try:
        result = graph.invoke({"messages": frequency})
        elapsed = time.time() - start
        articles = result.get("news_data", []) or []
        summary = result.get("summary", "") or ""
        usage = result.get("usage_metadata") or {}
        tokens = {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
        } if usage else {}
        target = {"daily": 30, "weekly": 45, "monthly": 60}.get(frequency.lower(), 60)
        path = logger.save(
            query=f"Fetch {frequency} AI news",
            response=summary,
            latency_seconds=elapsed,
            subcategory=frequency.lower(),
            frequency=frequency.lower(),
            article_count=len(articles),
            target_latency_seconds=target,
            within_target=elapsed <= target,
            **tokens,
        )
        return {"ok": True, "path": path, "latency": elapsed,
                "articles": len(articles), "tokens": tokens.get("total_tokens"),
                "preview": summary[:80]}
    except Exception as e:
        elapsed = time.time() - start
        path = logger.save(query=f"Fetch {frequency} AI news", response=f"ERROR: {e}",
                           latency_seconds=elapsed, subcategory=frequency.lower(), error=str(e)[:300])
        return {"ok": False, "path": path, "latency": elapsed, "error": str(e)[:200]}


def main():
    overall_start = time.time()
    total = 0
    failed = 0

    print("=" * 70)
    print("BATCH EVALUATION RUN")
    print("=" * 70)

    for model_name in MODELS:
        print(f"\n{'#' * 70}\n# MODEL: {model_name}\n{'#' * 70}")
        try:
            llm = make_llm(model_name)
        except Exception as e:
            print(f"  [FAIL] LLM init failed: {e}")
            continue

        # ---- Basic Chatbot ----
        print(f"\n[Basic Chatbot] {len(BASIC_CHATBOT_PROMPTS)} prompts")
        for i, prompt in enumerate(BASIC_CHATBOT_PROMPTS, 1):
            r = run_basic_chatbot(model_name, prompt, llm)
            total += 1
            ok = "OK  " if r["ok"] else "FAIL"
            if not r["ok"]:
                failed += 1
            print(f"  {ok} [{i}/{len(BASIC_CHATBOT_PROMPTS)}] {r['latency']:.1f}s "
                  f"{r.get('preview','') or r.get('error','')}")
            time.sleep(1)

        # ---- Chatbot With Web ----
        web_set = [(p, True) for p in WEB_PROMPTS_TRIGGER] + [(p, False) for p in WEB_PROMPTS_NO_TRIGGER]
        print(f"\n[Chatbot With Web] {len(web_set)} prompts (5 trigger + 5 no-trigger)")
        for i, (prompt, expected) in enumerate(web_set, 1):
            r = run_chatbot_with_web(model_name, prompt, expected, llm)
            total += 1
            ok = "OK  " if r["ok"] else "FAIL"
            if not r["ok"]:
                failed += 1
            extra = ""
            if r.get("ok"):
                extra = f"tool={r['tool_used']} (expected={r['expected']}) {'route_ok' if r['correct'] else 'route_fail'}"
            print(f"  {ok} [{i:>2}/{len(web_set)}] {r['latency']:.1f}s {extra} {r.get('preview','') or r.get('error','')}")
            time.sleep(1)

        # ---- AI News ----
        print(f"\n[AI News] frequencies: {AI_NEWS_FREQUENCIES}")
        for freq in AI_NEWS_FREQUENCIES:
            r = run_ai_news(model_name, freq, llm)
            total += 1
            ok = "OK  " if r["ok"] else "FAIL"
            if not r["ok"]:
                failed += 1
            extra = f"articles={r.get('articles', 0)}, tokens={r.get('tokens')}" if r["ok"] else r.get("error", "")
            print(f"  {ok} {freq:8s} {r['latency']:.1f}s  {extra}")
            time.sleep(2)

    elapsed = time.time() - overall_start
    print(f"\n{'=' * 70}\nDONE: {total - failed}/{total} runs OK · failed={failed} · elapsed={elapsed:.1f}s")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
