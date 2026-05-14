"""
MQTT Publisher
Responsible: Member 2

Publishes processed drone detection messages to an MQTT topic.
"""

import json
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "drones/detections"


def create_sample_message():
    return {
        "drone_id": "drone_1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "object": "tree",
        "distance": 8,
        "direction": "front",
        "confidence": 0.89,
        "location": [34.5, -118.2, 15.0],
    }


def main():
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)

    while True:
        message = create_sample_message()
        payload = json.dumps(message)
        client.publish(TOPIC, payload)
        print(f"Published to {TOPIC}: {payload}")
        time.sleep(5)


if __name__ == "__main__":
    main()
