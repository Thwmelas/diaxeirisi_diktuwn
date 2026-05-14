# LLM Decision Module

## Responsible Member
Member 3

## Purpose
This module receives structured drone messages and returns a decision in JSON format.

## Main Responsibilities
- Build prompts for the LLM.
- Interpret drone detection messages.
- Produce risk level, action, recommendation and broadcast decision.
- Provide rule-based fallback if the LLM is unavailable or returns invalid JSON.
- Test the module with sample drone scenarios.

## Input Example
```json
{
  "drone_id": "drone_1",
  "object": "tree",
  "distance": 8,
  "direction": "front",
  "confidence": 0.89
}
```

## Output Example
```json
{
  "risk_level": "high",
  "action": "avoid_obstacle",
  "recommendation": "Obstacle very close at front. Stop and change direction.",
  "broadcast": true
}
```

## How to Run
```bash
python llm_module/test_scenarios.py
```
