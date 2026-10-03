"""
Unit tests for the LLM decision module (no real LLM needed).
Run from the project root:  pytest tests/test_llm_module.py -v
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llm_module.llm_client import LLMUnavailable, OllamaClient
from llm_module.llm_decision import DecisionEngine, decide_with_details, interpret_drone_message
from llm_module.rule_based_fallback import rule_based_decision
from llm_module.safety import apply_safety_override
from llm_module.scenarios import SCENARIOS
from llm_module.schema import InvalidDecision, parse_llm_json
from llm_module.swarm_context import SwarmContext, distance_m

TREE_CLOSE = {"drone_id": "drone_1", "object": "tree", "distance": 8, "direction": "front", "confidence": 0.89}
CAR_FAR = {"drone_id": "drone_1", "object": "car", "distance": 70, "direction": "back", "confidence": 0.8}


class FakeClient:
    """Stands in for Ollama: returns a fixed reply and records the prompts."""
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def complete(self, system, user):
        self.calls.append((system, user))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def reply(risk="low", action="continue_mission", rec="Continue.", broadcast=False):
    return json.dumps({"risk_level": risk, "action": action, "recommendation": rec, "broadcast": broadcast})


# --- schema / parsing ---------------------------------------------------------

def test_parse_plain_json():
    assert parse_llm_json(reply("high", "avoid_obstacle", "Stop.", True))["action"] == "avoid_obstacle"


def test_parse_strips_code_fences_and_prose():
    text = "Sure! ```json\n" + reply("medium", "adjust_course") + "\n```"
    assert parse_llm_json(text)["risk_level"] == "medium"


def test_parse_normalizes_values():
    d = parse_llm_json('{"risk_level":"HIGH","action":"Avoid Obstacle","recommendation":"x","broadcast":"true"}')
    assert d == {"risk_level": "high", "action": "avoid_obstacle", "recommendation": "x", "broadcast": True}


@pytest.mark.parametrize("bad", [
    "", "not json", "[1,2]",
    '{"risk_level":"high","action":"avoid_obstacle","recommendation":"x"}',               # missing field
    '{"risk_level":"extreme","action":"avoid_obstacle","recommendation":"x","broadcast":true}',
    '{"risk_level":"high","action":"self_destruct","recommendation":"x","broadcast":true}',
    '{"risk_level":"high","action":"avoid_obstacle","recommendation":"x","broadcast":"maybe"}',
])
def test_parse_rejects_invalid(bad):
    with pytest.raises(InvalidDecision):
        parse_llm_json(bad)


# --- rules ----------------------------------------------------------------------

def test_rules_handle_broken_input():
    d = rule_based_decision({"object": None, "distance": "far", "confidence": "high"})
    assert d["action"] == "continue_mission"


def test_rules_backward_compatible_examples():
    path = Path(__file__).resolve().parents[1] / "llm_module" / "drone_llm_examples.jsonl"
    for line in path.read_text().splitlines()[:3]:
        ex = json.loads(line)
        assert ex["output"]  # file is readable JSONL
    assert rule_based_decision(TREE_CLOSE)["risk_level"] == "high"


# --- LLM path -------------------------------------------------------------------

def test_llm_decision_accepted():
    client = FakeClient(reply("low", "adjust_course", "Go around the car.", False))
    d = decide_with_details(CAR_FAR, client)
    assert d["decision"]["source"] == "llm"
    assert d["decision"]["recommendation"] == "Go around the car."


def test_fallback_when_llm_unreachable():
    d = decide_with_details(TREE_CLOSE, FakeClient(LLMUnavailable("down")))
    assert d["decision"]["source"] == "rules"
    assert d["decision"]["action"] == "avoid_obstacle"
    assert "LLMUnavailable" in d["error"]


def test_fallback_when_llm_returns_garbage():
    d = decide_with_details(TREE_CLOSE, FakeClient("I think you should fly away"))
    assert d["decision"]["source"] == "rules"


def test_safety_overrides_unsafe_llm():
    # LLM says "all fine" with a tree 8 m in front: must be corrected.
    d = decide_with_details(TREE_CLOSE, FakeClient(reply()))
    dec = d["decision"]
    assert dec["source"] == "llm+safety"
    assert (dec["risk_level"], dec["action"], dec["broadcast"]) == ("high", "avoid_obstacle", True)
    assert "close_obstacle_action" in d["overrides"]


def test_safety_allows_escalation():
    # LLM is MORE cautious than rules: allowed, no override.
    final, overrides = apply_safety_override(CAR_FAR, parse_llm_json(reply("high", "hover_and_monitor", "Watch.", True)))
    assert overrides == [] and final["risk_level"] == "high"


def test_confirmed_fire_is_always_high():
    fire = {"object": "fire", "distance": 60, "confidence": 0.9, "direction": "left"}
    final, overrides = apply_safety_override(fire, parse_llm_json(reply("medium", "notify_swarm", "x", False)))
    assert final["risk_level"] == "high" and final["broadcast"] is True
    assert {"hazard_risk", "hazard_broadcast"} <= set(overrides)


def test_interpret_default_is_rules_only():
    assert interpret_drone_message(TREE_CLOSE)["source"] == "rules"


# --- swarm context --------------------------------------------------------------

def test_context_excludes_own_drone_and_old_messages():
    ctx = SwarmContext(max_age_s=30)
    ctx.add({"drone_id": "drone_2", "object": "smoke", "timestamp": "2026-01-15T12:00:00Z"})  # too old
    ctx.add({"drone_id": "drone_1", "object": "tree", "timestamp": "2026-01-15T12:00:50Z"})   # self
    ctx.add({"drone_id": "drone_3", "object": "fire", "timestamp": "2026-01-15T12:00:55Z"})
    summary = ctx.summary({"drone_id": "drone_1", "timestamp": "2026-01-15T12:01:00Z"})
    assert "drone_3" in summary and "drone_1" not in summary and "smoke" not in summary


def test_context_reaches_prompt():
    sc = next(s for s in SCENARIOS if s["name"] == "smoke_confirmed_by_swarm")
    ctx = SwarmContext()
    for m in sc["context"]:
        ctx.add(m)
    client = FakeClient(reply("high", "hover_and_monitor", "Smoke confirmed. Hold and monitor.", True))
    decide_with_details(sc["message"], client, ctx)
    user_prompt = client.calls[0][1]
    assert "drone_2" in user_prompt and "drone_3" in user_prompt and "m from this drone" in user_prompt


def test_distance_m():
    assert distance_m([34.5, -118.2], [34.5, -118.2]) == 0
    assert 100 < distance_m([34.5, -118.2], [34.501, -118.2]) < 120   # ~111 m
    assert distance_m(None, [1, 2]) is None


def test_engine_remembers_messages():
    client = FakeClient(reply("low", "continue_mission", "ok", False))
    engine = DecisionEngine(client=client)
    engine.process({"drone_id": "drone_2", "object": "smoke", "distance": 30, "confidence": 0.9,
                    "timestamp": "2026-01-15T12:00:00Z"})
    engine.process({"drone_id": "drone_1", "object": "car", "distance": 50, "confidence": 0.8,
                    "timestamp": "2026-01-15T12:00:05Z"})
    assert "drone_2: smoke" in client.calls[1][1]
    assert "No recent reports" in client.calls[0][1]


# --- Ollama client against a fake HTTP server -----------------------------------

@pytest.fixture
def fake_ollama():
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            body = json.dumps({"models": [{"name": "llama3.2:3b"}]}).encode()
            self.send_response(200); self.end_headers(); self.wfile.write(body)

        def do_POST(self):
            received.update(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            body = json.dumps({"message": {"role": "assistant",
                                           "content": reply("high", "avoid_obstacle", "Stop.", True)}}).encode()
            self.send_response(200); self.end_headers(); self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", received
    server.shutdown()


def test_ollama_client_roundtrip(fake_ollama):
    url, received = fake_ollama
    client = OllamaClient(model="llama3.2:3b", url=url, json_schema={"type": "object"})
    assert client.is_available()
    d = interpret_drone_message(TREE_CLOSE, use_llm=True, client=client)
    assert d["source"] == "llm" and d["action"] == "avoid_obstacle"
    assert received["stream"] is False and received["format"] == {"type": "object"}
    assert received["options"]["temperature"] == 0.0


def test_ollama_client_unreachable():
    client = OllamaClient(url="http://127.0.0.1:9", timeout=1)
    assert not client.is_available()
    with pytest.raises(LLMUnavailable):
        client.complete("s", "u")
