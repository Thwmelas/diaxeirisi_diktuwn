# AI-Enabled Drone Swarm Network and Information Management

## Project Summary
This project implements a modular drone swarm system focused on:

- Object detection using YOLO
- Drone-to-drone information exchange using MQTT
- LLM-based decision-making and message interpretation
- ROS2/Gazebo simulation and integration

The goal is to allow drones to process sensor data locally, exchange compact structured information, and build collaborative awareness.

---

## Team Work Distribution

| Member | Module | Main Responsibility | Folder |
|---|---|---|---|
| Member 1 | Object Detection | YOLO detection, image/video processing, detection JSON output | `object_detection/` |
| Member 2 | Communication | MQTT broker, publisher/subscriber, message exchange | `communication/` |
| Member 3 | LLM Decision Module | Interpret drone messages, produce decisions, fallback rules | `llm_module/` |
| Member 4 | Simulation & Integration | ROS2/Gazebo setup, multi-drone simulation, system integration | `simulation/`, `integration/` |

---

## Repository Structure

```text
ai-drone-swarm-project/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── object_detection/
│   ├── yolo_detector.py
│   └── README.md
│
├── communication/
│   ├── mqtt_publisher.py
│   ├── mqtt_subscriber.py
│   └── README.md
│
├── llm_module/
│   ├── llm_decision.py
│   ├── rule_based_fallback.py
│   ├── test_scenarios.py
│   ├── drone_llm_examples.jsonl
│   └── README.md
│
├── simulation/
│   ├── ros2_nodes/
│   ├── launch/
│   └── README.md
│
├── integration/
│   ├── demo_pipeline.py
│   └── README.md
│
├── docs/
│   ├── architecture.md
│   ├── message_format.md
│   ├── team_tasks.md
│   └── final_report_notes.md
│
└── tests/
    └── sample_messages.json
```

---

## Suggested Git Workflow

```bash
git checkout -b dev
```

Each member works on a separate branch:

```bash
git checkout -b feature/yolo
git checkout -b feature/mqtt
git checkout -b feature/llm
git checkout -b feature/ros2
```

When a feature is ready, open a Pull Request into `dev`. After integration testing, merge `dev` into `main`.

---

## Common Message Format

All modules should use the same structured message format:

```json
{
  "drone_id": "drone_1",
  "timestamp": "2026-01-15T12:30:00Z",
  "object": "tree",
  "distance": 8,
  "direction": "front",
  "confidence": 0.89,
  "location": [34.5, -118.2, 15.0]
}
```

The LLM module should return:

```json
{
  "risk_level": "high",
  "action": "avoid_obstacle",
  "recommendation": "Obstacle very close at front. Stop and change direction.",
  "broadcast": true
}
```
