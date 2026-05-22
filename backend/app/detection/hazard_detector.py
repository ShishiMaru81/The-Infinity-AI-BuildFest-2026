"""Ensemble hazard detection: YOLOv8 (+ optional custom weights) + Roboflow."""

import cv2
import numpy as np

from app.config import settings
from app.detection.class_map import HAZARD_CLASSES, normalize_label
from app.detection.roboflow_client import infer_roboflow
from app.vision.yolo_detector import YOLODetector

HAZARD_COLORS = {
    "knife": (0, 0, 255),
    "gun": (0, 0, 200),
    "fire": (0, 140, 255),
    "lighter": (255, 0, 255),
}


class HazardDetector:
    def __init__(self):
        self.yolo = YOLODetector(model_path=settings.yolo_model)

    async def detect(
        self,
        frame_bgr: np.ndarray,
        frame_b64: str,
        confidence_threshold: float | None = None,
    ) -> tuple[list[dict], np.ndarray, str | None, float]:
        """
        Returns: detections, annotated frame, best_hazard_class, max_confidence
        """
        threshold = confidence_threshold or settings.detection_confidence_threshold
        yolo_dets, annotated, _ = self.yolo.detect(frame_bgr)
        merged: list[dict] = []

        for d in yolo_dets:
            hazard = normalize_label(d["label"])
            if hazard and d["confidence"] >= threshold:
                merged.append(
                    {
                        "label": hazard,
                        "raw_label": d["label"],
                        "confidence": d["confidence"],
                        "bbox": d["bbox"],
                        "source": "yolo",
                    }
                )

        for model in (settings.roboflow_weapon_model, settings.roboflow_fire_model):
            if model:
                rf = await infer_roboflow(frame_b64, model)
                for d in rf:
                    if d["confidence"] >= threshold:
                        merged.append(d)

        merged = _dedupe(merged)
        annotated = _draw_hazards(frame_bgr, merged)

        best_hazard: str | None = None
        max_conf = 0.0
        for d in merged:
            if d["confidence"] > max_conf:
                max_conf = d["confidence"]
                best_hazard = d["label"]

        return merged, annotated, best_hazard, max_conf


def _dedupe(detections: list[dict], iou_thresh: float = 0.5) -> list[dict]:
    if not detections:
        return []
    detections = sorted(detections, key=lambda x: x["confidence"], reverse=True)
    kept: list[dict] = []
    for det in detections:
        if not any(_iou(det["bbox"], k["bbox"]) > iou_thresh and det["label"] == k["label"] for k in kept):
            kept.append(det)
    return kept


def _iou(a: list, b: list) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter <= 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter + 1e-6)


def _draw_hazards(frame_bgr: np.ndarray, detections: list[dict]) -> np.ndarray:
    out = frame_bgr.copy()
    for d in detections:
        x1, y1, x2, y2 = d["bbox"]
        color = HAZARD_COLORS.get(d["label"], (0, 255, 0))
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            out,
            f"{d['label']} {d['confidence']:.0%}",
            (x1, max(12, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )
    return out
