import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.dispatcher import run_dispatch
from app.agent.tools import log_incident_tool
from app.config import settings
from app.schemas import DispatchRequest, DispatchResponse
from app.utils import dispatch_log
from app.database import get_db
from app.models import Incident, SettingsRow
from app.schemas import IncidentCreate, IncidentResponse, SettingsUpdate
from app.services.video_processor import UPLOAD_DIR, process_video_file, video_jobs
from app.vision.pipeline import VisionPipeline

router = APIRouter()
pipeline = VisionPipeline()


@router.get("/health")
async def health():
    return {
        "status": "online",
        "service": "GuardianAI",
        "alert_mode": settings.alert_mode,
        "app_mode": settings.app_mode,
        "groq_configured": bool(settings.groq_api_key),
        "yolo_model": settings.yolo_model,
        "detection_threshold": settings.detection_confidence_threshold,
        "consecutive_frames": settings.detection_consecutive_frames,
        "version": "1.0.0",
    }


@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total_today = await db.scalar(
        select(func.count(Incident.id)).where(Incident.created_at >= today)
    )
    critical = await db.scalar(
        select(func.count(Incident.id)).where(
            Incident.priority == "CRITICAL", Incident.created_at >= today
        )
    )
    return {
        "incidents_today": total_today or 0,
        "critical_today": critical or 0,
        "active_cameras": 1,
        "system_status": "OPERATIONAL",
    }


@router.get("/incidents", response_model=list[IncidentResponse])
async def list_incidents(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Incident).order_by(Incident.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        from fastapi import HTTPException

        raise HTTPException(404, "Incident not found")
    return inc


@router.post("/incidents", response_model=IncidentResponse)
async def create_incident(data: IncidentCreate, db: AsyncSession = Depends(get_db)):
    logged = await log_incident_tool(data.model_dump(), db)
    result = await db.execute(select(Incident).where(Incident.id == logged["id"]))
    inc = result.scalar_one()
    return inc


@router.post("/dispatch", response_model=DispatchResponse)
async def dispatch_emergency(data: DispatchRequest, db: AsyncSession = Depends(get_db)):
    result = await run_dispatch(
        incident_id=data.incident_id,
        threat_type=data.threat_type,
        confidence=data.confidence,
        location=data.location,
        latitude=data.latitude,
        longitude=data.longitude,
        description=data.description,
        snapshot_b64=data.snapshot_b64,
        requested_mode=data.mode,
        db=db,
    )
    return DispatchResponse(**result)


@router.get("/dispatch/log")
async def get_dispatch_log(limit: int = 50):
    return dispatch_log.list_events(limit)


@router.post("/analyze/frame")
async def analyze_single_frame(
    frame_b64: str = Form(...),
    lat: float = Form(settings.default_lat),
    lng: float = Form(settings.default_lng),
):
    result = await pipeline.process_frame_b64(frame_b64)
    return result.model_dump()


@router.post("/video/upload")
async def upload_video(
    file: UploadFile = File(...),
    fps: int = Form(2),
    lat: float = Form(settings.default_lat),
    lng: float = Form(settings.default_lng),
):
    ext = Path(file.filename or "video.mp4").suffix.lower()
    if ext not in (".mp4", ".avi", ".mov", ".mkv"):
        from fastapi import HTTPException

        raise HTTPException(400, "Unsupported format. Use mp4, avi, mov.")
    path = UPLOAD_DIR / f"{datetime.utcnow().timestamp()}{ext}"
    with path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    job_id = await process_video_file(str(path), fps, lat, lng)
    return {"job_id": job_id, "status": "processing"}


@router.get("/video/job/{job_id}")
async def video_job_status(job_id: str):
    job = video_jobs.get(job_id)
    if not job:
        from fastapi import HTTPException

        raise HTTPException(404, "Job not found")
    return job


@router.post("/rtsp/start")
async def start_rtsp(url: str = Form(...), fps: int = Form(2)):
    import cv2

    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        from fastapi import HTTPException

        raise HTTPException(400, "Cannot connect to RTSP stream")
    cap.release()
    return {"status": "ok", "message": "RTSP validated. Connect via WebSocket with source=rtsp.", "url": url, "fps": fps}


@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    from app.services.hospitals import HOSPITALS

    result = await db.execute(select(SettingsRow))
    rows = {r.key: r.value for r in result.scalars().all()}
    hospitals = json.loads(rows.get("hospitals", "[]")) or HOSPITALS
    return {
        "alert_mode": rows.get("alert_mode", settings.alert_mode),
        "police_number": rows.get("police_number", settings.police_number),
        "app_mode": rows.get("app_mode", settings.app_mode),
        "hospitals": hospitals,
        "detection_confidence_threshold": float(
            rows.get("detection_confidence_threshold", settings.detection_confidence_threshold)
        ),
        "detection_consecutive_frames": int(
            rows.get("detection_consecutive_frames", settings.detection_consecutive_frames)
        ),
        "frame_fps": int(rows.get("frame_fps", settings.frame_fps)),
        "real_dispatch_cooldown_sec": int(
            rows.get("real_dispatch_cooldown_sec", settings.real_dispatch_cooldown_sec)
        ),
        "test_email": rows.get("test_email", settings.test_email),
        "fallback_address": rows.get("fallback_address", settings.fallback_address),
    }


@router.put("/settings")
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    async def upsert(key: str, value: str):
        r = await db.execute(select(SettingsRow).where(SettingsRow.key == key))
        row = r.scalar_one_or_none()
        if row:
            row.value = value
        else:
            db.add(SettingsRow(key=key, value=value))
        await db.commit()

    if data.hospitals:
        await upsert("hospitals", json.dumps(data.hospitals))
    if data.alert_mode:
        await upsert("alert_mode", data.alert_mode)
        settings.alert_mode = data.alert_mode
    if data.police_number:
        await upsert("police_number", data.police_number)
        settings.police_number = data.police_number
    if data.app_mode:
        await upsert("app_mode", data.app_mode)
        settings.app_mode = data.app_mode
    if data.detection_confidence_threshold is not None:
        await upsert("detection_confidence_threshold", str(data.detection_confidence_threshold))
        settings.detection_confidence_threshold = data.detection_confidence_threshold
    if data.detection_consecutive_frames is not None:
        await upsert("detection_consecutive_frames", str(data.detection_consecutive_frames))
        settings.detection_consecutive_frames = data.detection_consecutive_frames
    if data.frame_fps is not None:
        await upsert("frame_fps", str(data.frame_fps))
        settings.frame_fps = data.frame_fps
    if data.real_dispatch_cooldown_sec is not None:
        await upsert("real_dispatch_cooldown_sec", str(data.real_dispatch_cooldown_sec))
        settings.real_dispatch_cooldown_sec = data.real_dispatch_cooldown_sec
    if data.test_email:
        await upsert("test_email", data.test_email)
        settings.test_email = data.test_email
    if data.fallback_address:
        await upsert("fallback_address", data.fallback_address)
        settings.fallback_address = data.fallback_address
    return {"status": "updated"}


@router.post("/incidents/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        from fastapi import HTTPException

        raise HTTPException(404, "Not found")
    inc.alert_status = "ACKNOWLEDGED"
    inc.status = "ACKNOWLEDGED"
    await db.commit()
    return {"status": "acknowledged"}
