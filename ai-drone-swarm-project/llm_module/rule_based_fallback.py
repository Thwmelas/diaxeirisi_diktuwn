"""
Rule-Based Fallback
Responsible: Member 3

Deterministic decision rules. Used when no LLM is available, when the LLM
returns something invalid, and as the source of hard safety constraints that
the LLM is not allowed to weaken (see safety.py).
"""

from typing import Any, Dict

CLOSE_DISTANCE_M = 10.0
MIN_CONFIDENCE = 0.70
LOW_CONFIDENCE = 0.40

HAZARDS = {"fire", "smoke"}
PEOPLE = {"person"}
OBSTACLES = {"tree", "building", "car", "truck", "vehicle", "pole", "wire", "bird"}


def _num(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Read the fields we need with safe defaults (missing/broken values)."""
    return {
        "object": str(message.get("object") or "unknown").strip().lower(),
        "distance": _num(message.get("distance"), 999.0),
        "direction": str(message.get("direction") or "unknown").strip().lower(),
        "confidence": _num(message.get("confidence"), 0.0),
    }


def rule_based_decision(message: Dict[str, Any]) -> Dict[str, Any]:
    m = normalize_message(message)
    obj, distance, direction, confidence = m["object"], m["distance"], m["direction"], m["confidence"]

    # 1. Anything very close is a collision risk, whatever it is and however
    #    sure the detector is. Safety first.
    if distance <= CLOSE_DISTANCE_M:
        what = obj if obj != "unknown" else "Obstacle"
        return {
            "risk_level": "high",
            "action": "avoid_obstacle",
            "recommendation": f"{what.capitalize()} very close at {direction} ({distance:g} m). Stop and change direction.",
            "broadcast": True,
        }

    # 2. Hazards and people with a reliable detection.
    if obj in HAZARDS and confidence >= MIN_CONFIDENCE:
        return {
            "risk_level": "high",
            "action": "notify_swarm",
            "recommendation": f"{obj.capitalize()} detected at {direction}. Notify nearby drones and monitor the area.",
            "broadcast": True,
        }
    if obj in PEOPLE and confidence >= MIN_CONFIDENCE:
        return {
            "risk_level": "medium",
            "action": "notify_swarm",
            "recommendation": f"Person detected at {direction}. Notify nearby drones and monitor the area.",
            "broadcast": True,
        }

    # 3. Hazard or person seen with medium confidence: worth a closer look.
    if obj in HAZARDS | PEOPLE and confidence >= LOW_CONFIDENCE:
        return {
            "risk_level": "medium",
            "action": "investigate",
            "recommendation": f"Possible {obj} at {direction} (confidence {confidence:.2f}). Approach carefully to confirm.",
            "broadcast": False,
        }

    # 4. Static or moving obstacles at a safe distance.
    if obj in OBSTACLES and confidence >= LOW_CONFIDENCE:
        return {
            "risk_level": "medium" if distance <= 25 else "low",
            "action": "adjust_course",
            "recommendation": f"{obj.capitalize()} at {direction} ({distance:g} m). Adjust course and update awareness map.",
            "broadcast": True,
        }

    return {
        "risk_level": "low",
        "action": "continue_mission",
        "recommendation": "No critical risk detected. Continue mission.",
        "broadcast": False,
    }
