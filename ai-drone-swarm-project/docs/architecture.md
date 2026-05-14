# System Architecture

## Overview
The project is split into four main modules:

1. Object Detection
2. MQTT Communication
3. LLM Decision-Making
4. ROS2/Gazebo Simulation and Integration

## Data Flow

```text
Drone Camera / Sensor
        ↓
Object Detection Module
        ↓
Structured JSON Message
        ↓
MQTT Communication Layer
        ↓
LLM Decision Module
        ↓
Drone Action / Swarm Awareness Update
```

## Main Design Choice
Instead of sending raw image or sensor data, each drone sends only processed information. This reduces bandwidth usage and supports real-time collaboration.
