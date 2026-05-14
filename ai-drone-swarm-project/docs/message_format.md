# Common Message Format

All team members should use the same JSON format.

## Detection Message

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

## Decision Message

```json
{
  "risk_level": "high",
  "action": "avoid_obstacle",
  "recommendation": "Obstacle very close at front. Stop and change direction.",
  "broadcast": true
}
```

## Fields

| Field | Meaning |
|---|---|
| `drone_id` | Drone that produced the message |
| `timestamp` | Time of detection |
| `object` | Detected object class |
| `distance` | Approximate distance from drone |
| `direction` | Object direction relative to drone |
| `confidence` | Object detection confidence |
| `location` | GPS or simulated coordinates |
