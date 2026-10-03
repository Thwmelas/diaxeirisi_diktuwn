"""
Evaluation: rule engine vs LLM.
Responsible: Member 3

Runs every scenario through the rules and (optionally) one or more Ollama
models and reports, per engine:
    - accuracy against the hand-written expectations (risk + action)
    - accuracy on swarm-context scenarios only
    - valid JSON rate of the raw LLM output
    - how often the safety layer had to correct the LLM
    - latency (mean / p95)

Run from the project root:
    python -m llm_module.evaluate                               # rules only
    python -m llm_module.evaluate --models llama3.2:3b qwen2.5:3b

Results are written to llm_module/results/ (JSON + Markdown table you can
paste into the report).
"""

import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from llm_module.llm_decision import DECISION_JSON_SCHEMA, decide_with_details
from llm_module.scenarios import SCENARIOS
from llm_module.swarm_context import SwarmContext

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _matches(decision: Optional[Dict[str, Any]], expect: Dict[str, List[str]]) -> bool:
    return bool(decision) and decision["risk_level"] in expect["risk"] and decision["action"] in expect["actions"]


def run_engine(name: str, client: Optional[Any]) -> Dict[str, Any]:
    rows = []
    for sc in SCENARIOS:
        context = SwarmContext()
        for m in sc.get("context", []):
            context.add(m)
        d = decide_with_details(sc["message"], client, context)
        rows.append({
            "scenario": sc["name"],
            "has_context": bool(sc.get("context")),
            "final": d["decision"],
            "llm_raw_decision": d["llm_decision"],
            "correct_final": _matches(d["decision"], sc["expect"]),
            "correct_llm_raw": _matches(d["llm_decision"], sc["expect"]) if client else None,
            "overrides": d["overrides"],
            "error": d["error"],
            "latency_ms": d["latency_ms"],
        })

    n = len(rows)
    ctx_rows = [r for r in rows if r["has_context"]]
    summary = {
        "engine": name,
        "scenarios": n,
        "accuracy_final": sum(r["correct_final"] for r in rows) / n,
        "accuracy_context_scenarios": (sum(r["correct_final"] for r in ctx_rows) / len(ctx_rows)) if ctx_rows else None,
    }
    if client is not None:
        valid = [r for r in rows if r["llm_raw_decision"] is not None]
        latencies = sorted(r["latency_ms"] for r in rows if r["latency_ms"] is not None)
        summary.update({
            "valid_json_rate": len(valid) / n,
            "accuracy_llm_before_safety": (sum(bool(r["correct_llm_raw"]) for r in rows) / n),
            "safety_override_rate": sum(bool(r["overrides"]) for r in valid) / len(valid) if valid else None,
            "fallback_count": n - len(valid),
            "latency_mean_ms": round(statistics.mean(latencies), 1) if latencies else None,
            "latency_p95_ms": latencies[max(0, int(round(0.95 * len(latencies))) - 1)] if latencies else None,
        })
    return {"summary": summary, "rows": rows}


def pct(x: Optional[float]) -> str:
    return "-" if x is None else f"{100 * x:.0f}%"


def to_markdown(results: List[Dict[str, Any]]) -> str:
    header = ("| Engine | Accuracy | Swarm-context accuracy | LLM before safety | Valid JSON | "
              "Safety overrides | Fallbacks | Mean latency | p95 latency |\n"
              "|---|---|---|---|---|---|---|---|---|\n")
    lines = []
    for r in results:
        s = r["summary"]
        lines.append(
            f"| {s['engine']} | {pct(s['accuracy_final'])} | {pct(s['accuracy_context_scenarios'])} | "
            f"{pct(s.get('accuracy_llm_before_safety'))} | {pct(s.get('valid_json_rate'))} | "
            f"{pct(s.get('safety_override_rate'))} | {s.get('fallback_count', '-')} | "
            f"{s.get('latency_mean_ms') or '-'} ms | {s.get('latency_p95_ms') or '-'} ms |"
        )
    detail = ["\n\n### Per-scenario results\n",
              "| Scenario | " + " | ".join(r["summary"]["engine"] for r in results) + " |",
              "|---|" + "---|" * len(results)]
    for i, sc in enumerate(SCENARIOS):
        cells = []
        for r in results:
            row = r["rows"][i]
            mark = "✓" if row["correct_final"] else "✗"
            cells.append(f"{mark} {row['final']['risk_level']}/{row['final']['action']}")
        detail.append(f"| {sc['name']} | " + " | ".join(cells) + " |")
    return header + "\n".join(lines) + "\n".join(detail) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=[], help="Ollama models to evaluate")
    args = parser.parse_args()

    results = [run_engine("rules", None)]
    for model in args.models:
        from llm_module.llm_client import OllamaClient
        client = OllamaClient(model=model, json_schema=DECISION_JSON_SCHEMA)
        if not client.is_available():
            print(f"[skip] {client.name}: server not reachable or model not pulled (ollama pull {model})")
            continue
        print(f"Evaluating {client.name} ...")
        results.append(run_engine(client.name, client))

    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (RESULTS_DIR / f"eval_{stamp}.json").write_text(json.dumps(results, indent=2))
    md = to_markdown(results)
    (RESULTS_DIR / f"eval_{stamp}.md").write_text(md)
    print(md)
    print(f"Saved to {RESULTS_DIR}/eval_{stamp}.json and .md")


if __name__ == "__main__":
    main()
