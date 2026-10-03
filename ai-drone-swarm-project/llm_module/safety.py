"""
Safety layer.
Responsible: Member 3

The LLM may ESCALATE a decision (e.g. raise risk because of swarm context)
but must never WEAKEN a hard safety rule. This module enforces that by
comparing the LLM decision with the deterministic rules.
"""

from typing import Any, Dict, List, Tuple

from llm_module.rule_based_fallback import (
    CLOSE_DISTANCE_M, HAZARDS, MIN_CONFIDENCE, normalize_message, rule_based_decision,
)
from llm_module.schema import RISK_ORDER, max_risk


def apply_safety_override(
    message: Dict[str, Any], decision: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[str]]:
    """Return (safe_decision, list_of_overrides_applied)."""
    m = normalize_message(message)
    rules = rule_based_decision(message)
    final = dict(decision)
    overrides: List[str] = []

    # Rule A: imminent collision -> must avoid, high risk, broadcast.
    if m["distance"] <= CLOSE_DISTANCE_M:
        if final["action"] != "avoid_obstacle":
            final["action"] = "avoid_obstacle"
            final["recommendation"] = rules["recommendation"]
            overrides.append("close_obstacle_action")
        if final["risk_level"] != "high":
            final["risk_level"] = "high"
            overrides.append("close_obstacle_risk")
        if not final["broadcast"]:
            final["broadcast"] = True
            overrides.append("close_obstacle_broadcast")

    # Rule B: confirmed fire/smoke -> at least high and broadcast.
    if m["object"] in HAZARDS and m["confidence"] >= MIN_CONFIDENCE:
        if final["risk_level"] != "high":
            final["risk_level"] = "high"
            overrides.append("hazard_risk")
        if not final["broadcast"]:
            final["broadcast"] = True
            overrides.append("hazard_broadcast")

    # Rule C: never report lower risk than the rules for this message.
    if RISK_ORDER[final["risk_level"]] < RISK_ORDER[rules["risk_level"]]:
        final["risk_level"] = max_risk(final["risk_level"], rules["risk_level"])
        overrides.append("risk_floor")

    return final, overrides
