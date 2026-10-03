"""
Test scenarios for the LLM Decision Module.
Responsible: Member 3

Run from the project root:
    python -m llm_module.test_scenarios          # rules only
    python -m llm_module.test_scenarios --llm    # with Ollama
"""

import argparse
import json

from llm_module.llm_decision import DECISION_JSON_SCHEMA, decide_with_details
from llm_module.scenarios import SCENARIOS
from llm_module.swarm_context import SwarmContext


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="use Ollama")
    parser.add_argument("--model", default=None, help="Ollama model name")
    args = parser.parse_args()

    client = None
    if args.llm:
        from llm_module.llm_client import OllamaClient
        client = OllamaClient(model=args.model, json_schema=DECISION_JSON_SCHEMA)
        if not client.is_available():
            print(f"[warning] {client.name} not available, decisions will fall back to rules.\n")

    for sc in SCENARIOS:
        context = SwarmContext()
        for m in sc.get("context", []):
            context.add(m)
        d = decide_with_details(sc["message"], client, context)
        dec = d["decision"]
        ok = dec["risk_level"] in sc["expect"]["risk"] and dec["action"] in sc["expect"]["actions"]

        print(f"[{'OK ' if ok else 'BAD'}] {sc['name']}")
        print("  input:   ", json.dumps(sc["message"]))
        if sc.get("context"):
            print(f"  context:  {len(sc['context'])} reports from other drones")
        print("  decision:", json.dumps(dec))
        if d["overrides"]:
            print("  safety overrides:", ", ".join(d["overrides"]))
        if d["error"]:
            print("  llm error:", d["error"])
        print("-" * 70)


if __name__ == "__main__":
    main()
