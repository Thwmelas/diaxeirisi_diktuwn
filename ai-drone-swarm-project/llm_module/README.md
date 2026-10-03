# LLM Decision Module

## Responsible Member
Member 3

## Purpose
Receives structured drone messages and returns a decision in JSON format. A local
LLM (served by Ollama) interprets each message **together with recent reports from
other drones**, while a deterministic safety layer guarantees the LLM can never
weaken a hard safety rule. If the LLM is unavailable or answers incorrectly, the
module falls back to rule-based decisions, so it always returns a valid decision.

## Pipeline

```text
drone message ──┐
                ├─► prompt ─► LLM (Ollama) ─► parse + validate ─► safety layer ─► decision
swarm context ──┘                  │                │
                                   └── error ───────┴──► rule-based fallback ─► decision
```

## Files

| File | What it does |
|---|---|
| `llm_decision.py` | Main entry point: prompt building, `interpret_drone_message`, `DecisionEngine` |
| `llm_client.py` | Ollama client (standard library only, no extra dependency) |
| `schema.py` | Allowed risk levels/actions, JSON extraction and validation |
| `safety.py` | Corrects LLM decisions that are less safe than the hard rules |
| `rule_based_fallback.py` | Deterministic rules (fallback and safety reference) |
| `swarm_context.py` | Sliding window of recent messages from other drones |
| `scenarios.py` | 19 test scenarios with hand-written expected outcomes |
| `test_scenarios.py` | Prints the decision for every scenario |
| `evaluate.py` | Compares rules vs LLM models and writes result tables |
| `drone_llm_examples.jsonl` | Prompt/answer pairs for evaluation or fine-tuning |

Unit tests are in `tests/test_llm_module.py`.

## Input
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
Missing or broken fields are tolerated (safe defaults are used).

## Output
```json
{
  "risk_level": "high",
  "action": "avoid_obstacle",
  "recommendation": "Tree very close at front (8 m). Stop and change direction.",
  "broadcast": true,
  "source": "llm"
}
```

- `risk_level`: `low` | `medium` | `high`
- `action`: one of `avoid_obstacle`, `notify_swarm`, `adjust_course`, `hover_and_monitor`,
  `investigate`, `return_to_base`, `continue_mission`
- `source`: `rules` (no LLM / LLM failed), `llm` (accepted as-is), `llm+safety` (corrected by safety layer)

The four original fields are unchanged; `source` is extra and can be ignored by other modules.

## Setup

1. Install Ollama: https://ollama.com/download
2. Pull a small model:
   ```bash
   ollama pull llama3.2:3b
   ```
3. Optional configuration:
   ```bash
   export OLLAMA_MODEL=llama3.2:3b          # default
   export OLLAMA_URL=http://localhost:11434 # default
   ```

No extra Python package is needed for the LLM part.

## How to Run

All commands are run from the **project root** (`ai-drone-swarm-project/`).

```bash
# Decisions for all scenarios (rules only, works without Ollama)
python -m llm_module.test_scenarios

# Same, using the LLM
python -m llm_module.test_scenarios --llm

# Evaluation table for the report (compare several models)
python -m llm_module.evaluate --models llama3.2:3b qwen2.5:3b

# Unit tests (no LLM required)
pytest tests/test_llm_module.py -v
```

## Use from other modules

Single message, stateless:
```python
from llm_module.llm_decision import interpret_drone_message
decision = interpret_drone_message(message, use_llm=True)
```

Live use with swarm memory (recommended for the MQTT subscriber):
```python
from llm_module.llm_decision import DecisionEngine

engine = DecisionEngine(use_llm=True)   # create once

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    decision = engine.process(data)     # remembers previous messages
```

## Design Choices (for the report)

- **Hybrid LLM + rules.** The LLM adds reasoning over context (e.g. several drones
  reporting the same hazard); the rules guarantee predictable, safe behaviour.
- **The LLM can escalate, never downgrade.** If the LLM says "low risk" for an
  obstacle 5 m away, the safety layer overrides it. Every override is recorded.
- **Structured output.** A JSON schema is sent to Ollama, so the model is constrained
  to valid fields and a closed set of actions. Output is validated again in Python.
- **Always available.** Network errors, timeouts or invalid answers fall back to rules.
- **Swarm context.** Recent messages (last 60 s, max 50) from *other* drones are
  summarised in the prompt, including their distance from the current drone.
- **Local model.** Runs on-device or on a ground station, with no cloud dependency
  and no data leaving the system.

## Baseline results (rules only)

| Engine | Accuracy | Swarm-context accuracy |
|---|---|---|
| rules | 89% (17/19) | 33% (1/3) |

The rules fail only in the scenarios where another drone's report changes the
right answer (e.g. weak smoke detection confirmed by two nearby drones). This is
exactly the gap the LLM is meant to close. Run `evaluate.py` with your models to
fill in the LLM rows.
