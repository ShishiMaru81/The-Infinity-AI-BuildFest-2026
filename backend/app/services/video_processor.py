import asyncio
import os
import uuid
from pathlib import Path

import cv2

from app.config import settings
from app.vision.pipeline import VisionPipeline

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory job store for demo
video_jobs: dict[str, dict] = {}


async def process_video_file(
    file_path: str,
    fps: int | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> str:
    job_id = str(uuid.uuid4())
    video_jobs[job_id] = {
        "status": "processing",
        "timeline": [],
        "summary": {},
        "progress": 0,
    }
    asyncio.create_task(
        _run_video_job(job_id, file_path, fps or settings.frame_fps, lat, lng)
    )
    return job_id


async def _run_video_job(
    job_id: str,
    file_path: str,
    fps: int,
    lat: float | None,
    lng: float | None,
):
    pipeline = VisionPipeline()
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        video_jobs[job_id]["status"] = "error"
        video_jobs[job_id]["error"] = "Cannot open video"
        return

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    interval = max(1, int(video_fps / fps))
    frame_idx = 0
    timeline = []
    incident_counts: dict[str, int] = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval == 0:
            from app.vision.yolo_detector import YOLODetector

            b64 = YOLODetector.frame_to_b64(frame)
            result = await pipeline.process_frame_b64(b64)
            ts = frame_idx / video_fps
            if result.incident_type != "NORMAL":
                timeline.append(
                    {
                        "timestamp_sec": round(ts, 2),
                        "incident_type": result.incident_type,
                        "priority": result.priority,
                        "threat_level": result.threat_level,
                        "description": result.description,
                        "confidence": result.confidence,
                    }
                )
                incident_counts[result.incident_type] = (
                    incident_counts.get(result.incident_type, 0) + 1
                )
            video_jobs[job_id]["progress"] = min(
                99, int((frame_idx / max(1, cap.get(cv2.CAP_PROP_FRAME_COUNT)))) * 100
            )
        frame_idx += 1

    cap.release()
    video_jobs[job_id] = {
        "status": "completed",
        "timeline": timeline,
        "summary": {
            "total_frames_analyzed": frame_idx // interval,
            "incidents_by_type": incident_counts,
            "total_incidents": len(timeline),
            "location": {"lat": lat or settings.default_lat, "lng": lng or settings.default_lng},
        },
        "progress": 100,
    }


async def process_rtsp_stream(rtsp_url: str, duration_sec: int = 60, fps: int = 2):
    """Process RTSP for a limited duration; yields frames via callback pattern in WS handler."""
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise ValueError(f"Cannot connect to RTSP: {rtsp_url}")
    return cap
