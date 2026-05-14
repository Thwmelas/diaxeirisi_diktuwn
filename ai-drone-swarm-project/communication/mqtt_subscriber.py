"""
MQTT Subscriber
Responsible: Member 2

Receives drone messages and sends them to the LLM decision module.
"""

import json
import sys
from pathlib import Path

import paho.mqtt.client as mqtt

# Allow importing from project root when running this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from llm_module.llm_decision import interpret_drone_message

BROKER = "localhost"
PORT = 1883
TOPIC = "drones/detections"


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    print("Received:", data)

    decision = interpret_drone_message(data, use_llm=False)
    print("Decision:", json.dumps(decision, indent=2))


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
