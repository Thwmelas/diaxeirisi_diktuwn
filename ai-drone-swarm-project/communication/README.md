# Communication Module

## Responsible Member
Member 2

## Purpose
This module handles inter-drone communication using MQTT.

## Responsibilities
- Set up Mosquitto or another MQTT broker.
- Publish detection messages from one drone.
- Subscribe to detection topics from other drones.
- Forward received messages to the LLM decision module.

## Suggested Topics
- `drones/detections`
- `drones/alerts`
- `drones/decisions`
