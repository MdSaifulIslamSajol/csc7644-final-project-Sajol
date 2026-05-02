"""Response logger for evaluation.

Saves every LLM response as a markdown file under ./evaluations/ organized by
use case > model > optional sub-category, with YAML frontmatter capturing
latency, tokens, tool usage, and other metadata.
"""
import json
from datetime import datetime
from pathlib import Path

EVAL_ROOT = Path("./evaluations")


def _slug(s: str) -> str:
    return s.lower().replace(" ", "_").replace("/", "_")


class ResponseLogger:
    def __init__(self, usecase: str, model: str):
        self.usecase = usecase
        self.model = model

    def save(self, query, response, latency_seconds=None, subcategory=None, **extra):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        parts = [str(EVAL_ROOT), _slug(self.usecase), _slug(self.model)]
        if subcategory:
            parts.append(_slug(subcategory))
        folder = Path(*parts)
        folder.mkdir(parents=True, exist_ok=True)
        filepath = folder / f"{ts}.md"

        meta = {
            "usecase": self.usecase,
            "model": self.model,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "latency_seconds": round(latency_seconds, 2) if latency_seconds is not None else None,
        }
        if subcategory:
            meta["subcategory"] = subcategory
        meta.update({k: v for k, v in extra.items() if v is not None})

        with open(filepath, "w") as f:
            f.write("---\n")
            for k, v in meta.items():
                f.write(f"{k}: {json.dumps(v) if not isinstance(v, str) else v}\n")
            f.write("---\n\n")
            f.write(f"## Query\n\n{query}\n\n")
            f.write(f"## Response\n\n{response}\n")
        return str(filepath)


def extract_token_usage(ai_message):
    """Pulls token usage from a LangChain AIMessage if available."""
    try:
        usage = getattr(ai_message, "usage_metadata", None)
        if usage:
            return {
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens"),
            }
        meta = getattr(ai_message, "response_metadata", {}) or {}
        token_usage = meta.get("token_usage") or {}
        if token_usage:
            return {
                "input_tokens": token_usage.get("prompt_tokens"),
                "output_tokens": token_usage.get("completion_tokens"),
                "total_tokens": token_usage.get("total_tokens"),
            }
    except Exception:
        pass
    return {}
