"""
Object Detection Module
Responsible: Member 1

This script demonstrates YOLO-based object detection and converts detections
into the common JSON-like dictionary format used by the rest of the system.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

try:
    import cv2
    from ultralytics import YOLO
except ImportError:
    cv2 = None
    YOLO = None


def estimate_direction(x1: int, x2: int, frame_width: int) -> str:
    """Estimate object direction based on bounding box center."""
    center_x = (x1 + x2) / 2
    if center_x < frame_width / 3:
        return "left"
    if center_x > 2 * frame_width / 3:
        return "right"
    return "front"


def create_detection_message(
    drone_id: str,
    object_name: str,
    confidence: float,
    direction: str,
    distance: float = 15.0,
    location: List[float] | None = None,
) -> Dict[str, Any]:
    """Create the shared JSON message format for detections."""
    return {
        "drone_id": drone_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "object": object_name,
        "distance": distance,
        "direction": direction,
        "confidence": round(float(confidence), 3),
        "location": location or [0.0, 0.0, 0.0],
    }


def run_detection(source: int | str = 0, model_path: str = "yolov8n.pt", drone_id: str = "drone_1"):
    """Run real-time object detection from webcam or video file."""
    if YOLO is None or cv2 is None:
        raise ImportError("Install dependencies with: pip install ultralytics opencv-python")

    model = YOLO(model_path)
    cap = cv2.VideoCapture(source)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_height, frame_width = frame.shape[:2]
        results = model(frame)

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                label = model.names[class_id]
                direction = estimate_direction(x1, x2, frame_width)

                message = create_detection_message(
                    drone_id=drone_id,
                    object_name=label,
                    confidence=confidence,
                    direction=direction,
                )
                print(message)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {confidence:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow("YOLO Object Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_detection()
