"""
Decision schema and validation.
Responsible: Member 3

Defines the allowed values for a decision and turns raw LLM text into a
validated decision dictionary. Anything that does not match the schema is
rejected, so the caller can fall back to the rule-based engine.
"""

import json
import re
from typing import Any, Dict

RISK_LEVELS = ("low", "medium", "high")
RISK_ORDER = {level: i for i, level in enumerate(RISK_LEVELS)}

# Closed action vocabulary. Keeping it small makes the output predictable for
# the drones and easy to evaluate.
ACTIONS = {
    "avoid_obstacle": "Stop or change direction to avoid a nearby object.",
    "notify_swarm": "Alert nearby drones about something important.",
    "adjust_course": "Slightly change the planned route.",
    "hover_and_monitor": "Hold position and keep observing the target.",
    "investigate": "Move closer carefully to confirm an uncertain detection.",
    "return_to_base": "Abort the mission and fly back.",
    "continue_mission": "Nothing critical, keep going.",
}

REQUIRED_FIELDS = ("risk_level", "action", "recommendation", "broadcast")

# JSON schema passed to Ollama's structured output ("format" field).
DECISION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_level": {"type": "string", "enum": list(RISK_LEVELS)},
        "action": {"type": "string", "enum": list(ACTIONS)},
        "recommendation": {"type": "string"},
        "broadcast": {"type": "boolean"},
    },
    "required": list(REQUIRED_FIELDS),
}


class InvalidDecision(ValueError):
    """Raised when LLM output cannot be turned into a valid decision."""


def extract_json(text: str) -> Dict[str, Any]:
    """Parse JSON from LLM text, tolerating ```json fences or extra prose."""
    if not isinstance(text, str) or not text.strip():
        raise InvalidDecision("Empty LLM response")

    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Last resort: take the first {...} block in the text.
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise InvalidDecision("No JSON object found in LLM response")
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise InvalidDecision(f"Malformed JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise InvalidDecision("LLM response is not a JSON object")
    return data


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return value.strip().lower() == "true"
    raise InvalidDecision(f"broadcast must be a boolean, got {value!r}")


def validate_decision(data: Dict[str, Any]) -> Dict[str, Any]:
    """Check fields and values; return a clean decision with only known keys."""
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise InvalidDecision(f"Missing required field: {field}")

    risk = str(data["risk_level"]).strip().lower()
    if risk not in RISK_LEVELS:
        raise InvalidDecision(f"Invalid risk_level: {data['risk_level']!r}")

    action = str(data["action"]).strip().lower().replace(" ", "_").replace("-", "_")
    if action not in ACTIONS:
        raise InvalidDecision(f"Invalid action: {data['action']!r}")

    recommendation = str(data["recommendation"]).strip()
    if not recommendation:
        raise InvalidDecision("Empty recommendation")

    return {
        "risk_level": risk,
        "action": action,
        "recommendation": recommendation[:200],
        "broadcast": _to_bool(data["broadcast"]),
    }


def parse_llm_json(response: str) -> Dict[str, Any]:
    """Full pipeline: raw text -> validated decision (raises InvalidDecision)."""
    return validate_decision(extract_json(response))


def max_risk(a: str, b: str) -> str:
    return a if RISK_ORDER[a] >= RISK_ORDER[b] else b
