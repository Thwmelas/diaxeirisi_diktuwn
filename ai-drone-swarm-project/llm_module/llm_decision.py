"""
LLM Decision Module
Responsible: Member 3

Turns a structured drone message into a decision:

    {"risk_level": ..., "action": ..., "recommendation": ..., "broadcast": ..., "source": ...}

Pipeline:
    message (+ recent swarm reports)
      -> prompt -> LLM (Ollama) -> parse + validate
      -> safety override (LLM may escalate, never weaken hard rules)
      -> decision
    If the LLM is unreachable or its answer is invalid -> rule-based fallback.

The extra "source" field says where the decision came from:
    "rules"       rule-based engine (LLM disabled or failed)
    "llm"         LLM decision accepted as-is
    "llm+safety"  LLM decision corrected by the safety layer
"""

import json
import time
from typing import Any, Dict, Optional

from llm_module.rule_based_fallback import rule_based_decision
from llm_module.safety import apply_safety_override
from llm_module.schema import ACTIONS, DECISION_JSON_SCHEMA, parse_llm_json
from llm_module.swarm_context import SwarmContext

SYSTEM_PROMPT = """You are the decision-making module of an autonomous drone swarm.
You receive one detection report from a drone, plus recent reports from other drones.
Decide how the reporting drone should react. Reply with ONLY one JSON object.

Allowed actions:
{actions}

Guidelines:
- distance <= 10 m means imminent collision: risk_level "high", action "avoid_obstacle".
- fire or smoke with confidence >= 0.70: risk_level "high", broadcast true.
- person with confidence >= 0.70: at least "medium", usually "notify_swarm".
- Low confidence (< 0.40) detections are unreliable; do not overreact.
- Use the other drones' reports: if several drones report the same hazard nearby,
  that confirms it and may justify higher risk or "hover_and_monitor".
- broadcast true only if other drones should know about this.
- recommendation: one short imperative sentence, max 20 words.

Output format:
{{"risk_level": "low|medium|high", "action": "<one allowed action>", "recommendation": "<short command>", "broadcast": true|false}}"""


def build_system_prompt() -> str:
    actions = "\n".join(f"- {name}: {desc}" for name, desc in ACTIONS.items())
    return SYSTEM_PROMPT.format(actions=actions)


def build_user_prompt(message: Dict[str, Any], context_summary: str = "No recent reports from other drones.") -> str:
    fields = {k: message.get(k) for k in ("drone_id", "timestamp", "object", "distance",
                                          "direction", "confidence", "location") if k in message}
    return (
        f"Current report:\n{json.dumps(fields)}\n\n"
        f"Recent reports from other drones:\n{context_summary}\n\n"
        "Return the decision JSON."
    )


def build_prompt(message: Dict[str, Any], context_summary: str = "No recent reports from other drones.") -> str:
    """Single-string prompt (system + user), kept for compatibility and the report."""
    return build_system_prompt() + "\n\n" + build_user_prompt(message, context_summary)


def decide_with_details(
    message: Dict[str, Any],
    client: Optional[Any] = None,
    context: Optional[SwarmContext] = None,
) -> Dict[str, Any]:
    """
    Make a decision and return everything that happened (used for evaluation):
        decision, raw_llm, llm_decision, overrides, error, latency_ms
    """
    details: Dict[str, Any] = {
        "decision": None, "raw_llm": None, "llm_decision": None,
        "overrides": [], "error": None, "latency_ms": None,
    }

    if client is None:
        decision = rule_based_decision(message)
        decision["source"] = "rules"
        details["decision"] = decision
        return details

    summary = context.summary(message) if context is not None else "No recent reports from other drones."
    start = time.perf_counter()
    try:
        raw = client.complete(build_system_prompt(), build_user_prompt(message, summary))
        details["raw_llm"] = raw
        llm_decision = parse_llm_json(raw)
        details["llm_decision"] = dict(llm_decision)
    except Exception as exc:  # unreachable server, invalid JSON, bad values...
        details["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        details["error"] = f"{type(exc).__name__}: {exc}"
        decision = rule_based_decision(message)
        decision["source"] = "rules"
        details["decision"] = decision
        return details

    details["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
    final, overrides = apply_safety_override(message, llm_decision)
    final["source"] = "llm+safety" if overrides else "llm"
    details["overrides"] = overrides
    details["decision"] = final
    return details


def interpret_drone_message(
    message: Dict[str, Any],
    use_llm: bool = False,
    client: Optional[Any] = None,
    context: Optional[SwarmContext] = None,
) -> Dict[str, Any]:
    """
    Main entry point (same signature as before, extra args are optional).

    use_llm=False -> rules only.
    use_llm=True  -> LLM with safety layer; creates an OllamaClient if none given.
    """
    if use_llm and client is None:
        from llm_module.llm_client import OllamaClient
        client = OllamaClient(json_schema=DECISION_JSON_SCHEMA)
    return decide_with_details(message, client if use_llm else None, context)["decision"]


class DecisionEngine:
    """
    Stateful wrapper for live use (e.g. inside the MQTT subscriber).
    Remembers recent swarm messages and feeds them to the LLM as context.

        engine = DecisionEngine(use_llm=True)
        decision = engine.process(message)
    """

    def __init__(self, use_llm: bool = True, client: Optional[Any] = None,
                 context: Optional[SwarmContext] = None):
        self.context = context or SwarmContext()
        self.client = None
        if use_llm:
            if client is None:
                from llm_module.llm_client import OllamaClient
                client = OllamaClient(json_schema=DECISION_JSON_SCHEMA)
            self.client = client

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        details = decide_with_details(message, self.client, self.context)
        self.context.add(message)  # add AFTER deciding, so a drone doesn't see itself
        return details["decision"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run one sample decision.")
    parser.add_argument("--llm", action="store_true", help="use the LLM (Ollama) instead of rules only")
    args = parser.parse_args()

    sample_message = {
        "drone_id": "drone_1",
        "timestamp": "2026-01-15T12:30:00Z",
        "object": "tree",
        "distance": 8,
        "direction": "front",
        "confidence": 0.89,
        "location": [34.5, -118.2, 15.0],
    }
    print(json.dumps(interpret_drone_message(sample_message, use_llm=args.llm), indent=2))
