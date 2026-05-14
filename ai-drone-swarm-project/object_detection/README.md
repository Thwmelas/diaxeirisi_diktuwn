# Object Detection Module

## Responsible Member
Member 1

## Purpose
This module detects objects from a drone camera stream or image/video file using YOLO.

## Responsibilities
- Load YOLOv5/YOLOv8 model.
- Run detection on image or video frames.
- Extract object class, confidence, bounding box and approximate direction.
- Export detections as structured JSON for the MQTT module.

## Output Example
```json
{
  "drone_id": "drone_1",
  "object": "person",
  "distance": 12,
  "direction": "front",
  "confidence": 0.91,
  "location": [34.5, -118.2, 15.0]
}
```
