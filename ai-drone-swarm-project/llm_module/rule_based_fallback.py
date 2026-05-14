"""
Rule-Based Fallback
Responsible: Member 3

This file provides a safe fallback decision mechanism when the LLM is not
available or does not return valid JSON.
"""

from typing import Dict, Any


def rule_based_decision(message: Dict[str, Any]) -> Dict[str, Any]:
    obj = str(message.get("object", "unknown")).lower()
    distance = float(message.get("distance", 999))
    direction = message.get("direction", "unknown")
    confidence = float(message.get("confidence", 0))

    if distance <= 10:
        return {
            "risk_level": "high",
            "action": "avoid_obstacle",
            "recommendation": f"Obstacle very close at {direction}. Stop and change direction.",
            "broadcast": True,
        }

    if obj in ["person", "fire", "smoke"] and confidence >= 0.70:
        return {
            "risk_level": "high" if obj in ["fire", "smoke"] else "medium",
            "action": "notify_swarm",
            "recommendation": f"{obj} detected. Notify nearby drones and monitor the area.",
            "broadcast": True,
        }

    if obj in ["tree", "building", "car", "truck", "vehicle"]:
        return {
            "risk_level": "medium",
            "action": "adjust_course",
            "recommendation": f"{obj} detected. Adjust course and update awareness map.",
            "broadcast": True,
        }

    return {
        "risk_level": "low",
        "action": "continue_mission",
        "recommendation": "No critical risk detected. Continue mission.",
        "broadcast": False,
    }
