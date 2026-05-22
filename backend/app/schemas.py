from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DetectionObject(BaseModel):
    label: str
    confidence: float
    bbox: list[float]


class FrameAnalysisResult(BaseModel):
    incident_type: str
    priority: str
    threat_level: str
    confidence: float
    description: str
    detected_objects: list[DetectionObject]
    scene_analysis: dict[str, Any]
    recommended_action: str
    annotated_frame_b64: str | None = None
    should_alert: bool = False
    hazard_type: str | None = None
    hazard_confirmed: bool = False


class DispatchRequest(BaseModel):
    incident_id: int | None = None
    threat_type: str
    confidence: float
    location: str = "Dhaka, Bangladesh"
    latitude: float = 23.8103
    longitude: float = 90.4125
    description: str = ""
    snapshot_b64: str | None = None
    mode: str | None = None  # test | real


class DispatchResponse(BaseModel):
    status: str
    mode: str | None = None
    email: dict | None = None
    sms: dict | None = None
    call: dict | None = None
    log_id: str | None = None
    email_to: str | None = None
    reason: str | None = None
    cooldown_remaining_sec: int | None = None
    dispatch_status: dict | None = None


class IncidentCreate(BaseModel):
    incident_type: str
    priority: str
    threat_level: str
    description: str = ""
    location: str = "Dhaka, Bangladesh"
    latitude: float = 23.8103
    longitude: float = 90.4125
    confidence: float = 0.0
    detected_objects: list[dict] = Field(default_factory=list)
    scene_analysis: str = ""
    recommended_action: str = "none"
    source: str = "webcam"


class IncidentResponse(BaseModel):
    id: int
    incident_type: str
    priority: str
    threat_level: str
    status: str
    alert_status: str
    description: str
    location: str
    latitude: float
    longitude: float
    confidence: float
    detected_objects: str
    scene_analysis: str
    recommended_action: str
    agent_reasoning: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    hospitals: list[dict] = Field(default_factory=list)
    alert_mode: str | None = None
    police_number: str | None = None
    app_mode: str | None = None
    detection_confidence_threshold: float | None = None
    detection_consecutive_frames: int | None = None
    frame_fps: int | None = None
    real_dispatch_cooldown_sec: int | None = None
    test_email: str | None = None
    fallback_address: str | None = None


class VideoUploadResponse(BaseModel):
    job_id: str
    status: str


class TimelineEvent(BaseModel):
    timestamp_sec: float
    incident_type: str
    priority: str
    threat_level: str
    description: str
    confidence: float
