# Integration Module

## Responsible Member
Member 4, with support from all members

## Purpose
This folder contains scripts that connect the individual modules into one demo pipeline.

## Pipeline
```text
Camera/Image
    ↓
YOLO Object Detection
    ↓
Detection JSON
    ↓
MQTT Publish/Subscribe
    ↓
LLM Decision Module
    ↓
Action / Recommendation
```
