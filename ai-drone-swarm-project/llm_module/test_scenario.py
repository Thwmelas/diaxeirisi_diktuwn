"""
Test scenarios for the LLM Decision Module.
Responsible: Member 3
"""

import json
from llm_decision import interpret_drone_message

SCENARIOS = [
    {
        "drone_id": "drone_1",
        "object": "tree",
        "distance": 8,
        "direction": "front",
        "confidence": 0.89,
        "location": [34.5, -118.2, 15.0],
    },
    {
        "drone_id": "drone_2",
        "object": "person",
        "distance": 25,
        "direction": "left",
        "confidence": 0.92,
        "location": [34.6, -118.1, 15.0],
    },
    {
        "drone_id": "drone_3",
        "object": "smoke",
        "distance": 40,
        "direction": "right",
        "confidence": 0.80,
        "location": [34.7, -118.0, 15.0],
    },
]


def main():
    for scenario in SCENARIOS:
        decision = interpret_drone_message(scenario)
        print("Input:")
        print(json.dumps(scenario, indent=2))
        print("Decision:")
        print(json.dumps(decision, indent=2))
        print("-" * 50)


if __name__ == "__main__":
    main()
