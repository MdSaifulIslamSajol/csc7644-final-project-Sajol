"""Walk evaluations/ and produce per-model summary tables for each evaluation
dimension (functional completeness, latency, cost, tool orchestration).
"""
import json
import os
import csv
from pathlib import Path
from collections import defaultdict
from statistics import mean, median

EVAL_ROOT = Path("./evaluations")
OUT_CSV = Path("./evaluation_summary.csv")


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_block = text[4:end]
    body = text[end + 5:]
    meta = {}
    for line in fm_block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        try:
            meta[k.strip()] = json.loads(v)
        except Exception:
            meta[k.strip()] = v
    return meta, body


def load_records():
    records = []
    if not EVAL_ROOT.exists():
        return records
    for path in EVAL_ROOT.rglob("*.md"):
        with open(path) as f:
            text = f.read()
        meta, body = parse_frontmatter(text)
        meta["_path"] = str(path)
        meta["_response_chars"] = len(body)
        records.append(meta)
    return records


def fmt(v, w=10, dec=1):
    if v is None:
        return "n/a".ljust(w)
    if isinstance(v, float):
        return f"{v:.{dec}f}".ljust(w)
    return str(v).ljust(w)


def summary_table(records):
    by_model_uc = defaultdict(list)
    for r in records:
        key = (r.get("model", "?"), r.get("usecase", "?"))
        by_model_uc[key].append(r)

    print("\n" + "=" * 110)
    print(f"{'Model':<40}{'Use Case':<22}{'N':<5}{'Mean(s)':<10}{'Med(s)':<10}{'Tokens(avg)':<14}{'Errors':<8}")
    print("=" * 110)
    rows = []
    for (model, uc), recs in sorted(by_model_uc.items()):
        latencies = [r["latency_seconds"] for r in recs if isinstance(r.get("latency_seconds"), (int, float))]
        tokens = [r["total_tokens"] for r in recs if isinstance(r.get("total_tokens"), (int, float))]
        errors = sum(1 for r in recs if r.get("error") or str(r.get("response", "")).startswith("ERROR"))
        n = len(recs)
        row = {
            "model": model, "usecase": uc, "n": n,
            "mean_latency": mean(latencies) if latencies else None,
            "median_latency": median(latencies) if latencies else None,
            "mean_tokens": mean(tokens) if tokens else None,
            "errors": errors,
        }
        rows.append(row)
        print(f"{fmt(model, 40)}{fmt(uc, 22)}{fmt(n, 5, 0)}"
              f"{fmt(row['mean_latency'], 10)}{fmt(row['median_latency'], 10)}"
              f"{fmt(row['mean_tokens'], 14, 0)}{fmt(errors, 8, 0)}")
    return rows


def tool_routing_report(records):
    print("\n" + "=" * 80)
    print("TOOL ORCHESTRATION (Chatbot With Web)")
    print("=" * 80)
    print(f"{'Model':<40}{'N':<4}{'Correct':<10}{'Accuracy':<12}{'Tool used':<12}")
    print("-" * 80)
    by_model = defaultdict(list)
    for r in records:
        if r.get("usecase") != "Chatbot With Web":
            continue
        if "routing_correct" in r:
            by_model[r.get("model", "?")].append(r)
    rows = []
    for model, recs in sorted(by_model.items()):
        n = len(recs)
        correct = sum(1 for r in recs if r.get("routing_correct"))
        tool_used = sum(1 for r in recs if r.get("tool_used"))
        acc = (correct / n * 100) if n else 0
        rows.append({"model": model, "n": n, "correct": correct, "accuracy_pct": acc, "tool_used": tool_used})
        print(f"{fmt(model, 40)}{fmt(n, 4, 0)}{fmt(correct, 10, 0)}"
              f"{fmt(acc, 12, 1)}{fmt(tool_used, 12, 0)}")
    return rows


def ai_news_targets(records):
    print("\n" + "=" * 80)
    print("AI NEWS LATENCY vs TARGETS")
    print("=" * 80)
    print(f"{'Model':<40}{'Freq':<10}{'Latency(s)':<14}{'Target(s)':<12}{'Within?':<10}")
    print("-" * 80)
    rows = []
    for r in sorted([x for x in records if x.get("usecase") == "AI News"], key=lambda r: (r.get("model"), r.get("frequency", ""))):
        within = r.get("within_target")
        flag = "OK" if within else "MISS"
        rows.append(r)
        print(f"{fmt(r.get('model'), 40)}{fmt(r.get('frequency'), 10)}"
              f"{fmt(r.get('latency_seconds'), 14)}{fmt(r.get('target_latency_seconds'), 12)}"
              f"{fmt(flag, 10)}")
    return rows


def write_csv(rows, path):
    if not rows:
        return
    fields = sorted({k for r in rows for k in r.keys()})
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nwrote {path}")


def main():
    records = load_records()
    print(f"Loaded {len(records)} log records from {EVAL_ROOT}")

    summary = summary_table(records)
    routing = tool_routing_report(records)
    ai_news = ai_news_targets(records)

    write_csv(summary, OUT_CSV)


if __name__ == "__main__":
    main()
