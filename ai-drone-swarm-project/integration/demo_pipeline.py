"""
Demo Integration Pipeline
Responsible: Member 4, with input from all members

This script demonstrates the logical connection between object detection,
communication and LLM decision-making without requiring a full ROS2 setup.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from llm_module.llm_decision import interpret_drone_message


def main():
    # Simulated detection output from the YOLO module.
    detection_message = {
        "drone_id": "drone_1",
        "timestamp": "2026-01-15T12:30:00Z",
        "object": "building",
        "distance": 6,
        "direction": "front",
        "confidence": 0.95,
        "location": [34.5, -118.2, 15.0],
    }

    print("Detection message:")
    print(json.dumps(detection_message, indent=2))

    # Simulated LLM decision.
    decision = interpret_drone_message(detection_message)

    print("Decision:")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
