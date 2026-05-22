import base64
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# COCO class mapping for threat-relevant objects
WEAPON_KEYWORDS = {"knife", "scissors", "baseball bat", "tennis racket"}
FIRE_KEYWORDS = {"fire", "smoke"}
VEHICLE_KEYWORDS = {"car", "truck", "bus", "motorcycle", "bicycle"}

INCIDENT_MAP = {
    "weapon": "WEAPON_DETECTED",
    "violence": "VIOLENCE",
    "fire": "FIRE",
    "accident": "ACCIDENT",
    "person": "SUSPICIOUS_ACTIVITY",
}


class YOLODetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model = None
        self.model_path = model_path
        self._loaded = False

    def _ensure_model(self):
        if not self._loaded:
            from ultralytics import YOLO

            self.model = YOLO(self.model_path)
            self._loaded = True

    def detect(self, frame_bgr: np.ndarray) -> tuple[list[dict], np.ndarray, float]:
        self._ensure_model()
        results = self.model(frame_bgr, verbose=False)[0]
        detections = []
        max_conf = 0.0

        annotated = frame_bgr.copy()
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = results.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            threat = self._classify_label(label)
            detections.append(
                {
                    "label": label,
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2],
                    "threat_category": threat,
                }
            )
            max_conf = max(max_conf, conf)
            color = (0, 0, 255) if threat in ("weapon", "fire", "violence") else (0, 255, 0)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated,
                f"{label} {conf:.0%}",
                (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

        return detections, annotated, max_conf

    def _classify_label(self, label: str) -> str:
        low = label.lower()
        if any(w in low for w in WEAPON_KEYWORDS) or low in ("gun", "knife", "bat"):
            return "weapon"
        if any(w in low for w in FIRE_KEYWORDS):
            return "fire"
        if low in ("person", "people"):
            return "person"
        if any(w in low for w in VEHICLE_KEYWORDS):
            return "vehicle"
        return "other"

    @staticmethod
    def frame_to_b64(frame_bgr: np.ndarray) -> str:
        _, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return base64.b64encode(buf).decode("utf-8")

    @staticmethod
    def b64_to_frame(b64: str) -> np.ndarray:
        data = base64.b64decode(b64)
        arr = np.frombuffer(data, np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
