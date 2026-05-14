"""
LLM Decision Module
Responsible: Member 3

This module converts structured drone messages into decision outputs.
It can use an actual LLM later, but for the first working version it includes
prompt construction and a rule-based fallback.
"""

import json
from typing import Dict, Any

from llm_module.rule_based_fallback import rule_based_decision


def build_prompt(message: Dict[str, Any]) -> str:
    """Create a strict prompt for the LLM."""
    return f"""
You are an AI decision-making assistant for a drone swarm.

Analyze the following drone message and return ONLY valid JSON.

Drone message:
{json.dumps(message, indent=2)}

Rules:
- If distance is less than or equal to 10 meters, risk_level should be high.
- If the object is person, fire, smoke, car, truck, building or tree, broadcast should usually be true.
- Keep the recommendation short and actionable.
- Do not include explanations outside the JSON.

Return format:
{{
  "risk_level": "low | medium | high",
  "action": "short_action_name",
  "recommendation": "short command",
  "broadcast": true
}}
""".strip()


def call_llm_placeholder(prompt: str) -> str:
    """
    Placeholder for a real LLM call.

    Later this can be replaced with Hugging Face Transformers, Ollama,
    llama.cpp, OpenAI API, or another local/cloud model.
    """
    raise NotImplementedError("Real LLM call has not been connected yet.")


def parse_llm_json(response: str) -> Dict[str, Any]:
    """Parse LLM output and validate required fields."""
    data = json.loads(response)
    required_fields = ["risk_level", "action", "recommendation", "broadcast"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    return data


def interpret_drone_message(message: Dict[str, Any], use_llm: bool = False) -> Dict[str, Any]:
    """
    Main function for the LLM module.

    Input: structured drone message.
    Output: decision dictionary.
    """
    if not use_llm:
        return rule_based_decision(message)

    prompt = build_prompt(message)

    try:
        response = call_llm_placeholder(prompt)
        return parse_llm_json(response)
    except Exception:
        # Safety fallback: the system still returns a valid decision.
        return rule_based_decision(message)


if __name__ == "__main__":
    sample_message = {
        "drone_id": "drone_1",
        "object": "tree",
        "distance": 8,
        "direction": "front",
        "confidence": 0.89,
        "location": [34.5, -118.2, 15.0],
    }

    decision = interpret_drone_message(sample_message)
    print(json.dumps(decision, indent=2))
