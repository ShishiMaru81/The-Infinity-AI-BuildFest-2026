import json

from app.config import settings
from app.detection.class_map import INCIDENT_BY_HAZARD, PRIORITY_BY_HAZARD
from app.detection.frame_tracker import HazardFrameTracker
from app.detection.hazard_detector import HazardDetector
from app.schemas import DetectionObject, FrameAnalysisResult
from app.vision.claude_vision import ClaudeVisionAnalyzer
from app.vision.yolo_detector import YOLODetector

PRIORITY_MAP = {
    "WEAPON_DETECTED": "CRITICAL",
    "VIOLENCE": "HIGH",
    "ACCIDENT": "HIGH",
    "FIRE": "CRITICAL",
    "SUSPICIOUS_ACTIVITY": "MEDIUM",
    "NORMAL": "LOW",
}


class VisionPipeline:
    def __init__(self):
        self.hazard = HazardDetector()
        self.claude = ClaudeVisionAnalyzer()
        self.tracker = HazardFrameTracker(settings.detection_consecutive_frames)

    async def process_frame_b64(self, frame_b64: str) -> FrameAnalysisResult:
        self.tracker.required_frames = settings.detection_consecutive_frames
        frame = YOLODetector.b64_to_frame(frame_b64)
        threshold = settings.detection_confidence_threshold

        detections, annotated, best_hazard, max_conf = await self.hazard.detect(
            frame, frame_b64, confidence_threshold=threshold
        )
        annotated_b64 = YOLODetector.frame_to_b64(annotated)

        hazard_confirmed = False
        hazard_type: str | None = None

        if best_hazard and max_conf >= threshold:
            if self.tracker.update(best_hazard, max_conf):
                hazard_confirmed = True
                hazard_type = best_hazard
        else:
            self.tracker.tick_miss()

        yolo_summary = ", ".join(
            f"{d['label']}({d['confidence']:.0%})" for d in detections[:10]
        ) or "none"

        if hazard_confirmed:
            scene = {
                "happening": f"Confirmed {hazard_type} detection",
                "threat_level": "CRITICAL",
                "incident_type": "weapon" if hazard_type in ("knife", "gun", "lighter") else "fire",
                "recommended_action": "alert_police",
                "description": f"Hazard '{hazard_type}' confirmed over {settings.detection_consecutive_frames} frames.",
            }
        else:
            scene = await self.claude.analyze(annotated_b64, yolo_summary)

        if hazard_confirmed and hazard_type:
            incident_type = INCIDENT_BY_HAZARD.get(hazard_type, "WEAPON_DETECTED")
            priority = PRIORITY_BY_HAZARD.get(hazard_type, "CRITICAL")
            threat_level = "CRITICAL"
            confidence = max_conf
            description = scene.get("description", "")
        else:
            incident_type, priority, threat_level = self._combine_legacy(detections, scene, max_conf)
            confidence = max(max_conf, self._threat_to_conf(scene.get("threat_level", "SAFE")))
            description = scene.get("description", scene.get("happening", ""))

        recommended = scene.get("recommended_action", "none")
        should_alert = hazard_confirmed

        objects = [
            DetectionObject(label=d["label"], confidence=d["confidence"], bbox=d["bbox"])
            for d in detections
        ]

        return FrameAnalysisResult(
            incident_type=incident_type,
            priority=priority,
            threat_level=threat_level,
            confidence=confidence,
            description=description,
            detected_objects=objects,
            scene_analysis=scene,
            recommended_action=recommended,
            annotated_frame_b64=annotated_b64,
            should_alert=should_alert,
            hazard_type=hazard_type,
            hazard_confirmed=hazard_confirmed,
        )

    def _combine_legacy(self, detections, scene: dict, yolo_conf: float):
        yolo_incident = "NORMAL"
        for d in detections:
            label = d.get("label", "")
            if label in ("knife", "gun", "lighter"):
                yolo_incident = "WEAPON_DETECTED"
                break
            if label == "fire":
                yolo_incident = "FIRE"
                break

        claude_map = {
            "weapon": "WEAPON_DETECTED",
            "violence": "VIOLENCE",
            "accident": "ACCIDENT",
            "fire": "FIRE",
            "normal": "NORMAL",
        }
        claude_type = scene.get("incident_type", "normal").lower()
        claude_incident = claude_map.get(claude_type, "NORMAL")
        threat = scene.get("threat_level", "SAFE")

        severity = {
            "WEAPON_DETECTED": 5,
            "FIRE": 5,
            "VIOLENCE": 4,
            "ACCIDENT": 4,
            "SUSPICIOUS_ACTIVITY": 2,
            "NORMAL": 0,
        }
        final = (
            yolo_incident
            if severity.get(yolo_incident, 0) >= severity.get(claude_incident, 0)
            else claude_incident
        )
        if threat in ("DANGER", "CRITICAL") and severity.get(final, 0) < 4:
            final = claude_incident if claude_incident != "NORMAL" else final

        priority = PRIORITY_MAP.get(final, "LOW")
        return final, priority, threat

    @staticmethod
    def _threat_to_conf(level: str) -> float:
        return {"SAFE": 0.2, "SUSPICIOUS": 0.5, "DANGER": 0.75, "CRITICAL": 0.95}.get(
            level, 0.3
        )
