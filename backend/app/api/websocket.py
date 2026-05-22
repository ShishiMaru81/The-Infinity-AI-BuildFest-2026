import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent.tools import log_incident_tool
from app.config import settings
from app.database import async_session
from app.vision.pipeline import VisionPipeline

router = APIRouter()
pipeline = VisionPipeline()

_last_analysis = 0.0
_min_interval = 1.0 / max(1, settings.frame_fps)


@router.websocket("/ws/live")
async def live_feed_ws(websocket: WebSocket):
    await websocket.accept()
    global _last_analysis

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg.get("type") != "frame":
                continue

            frame_b64 = msg.get("frame")
            if not frame_b64:
                continue

            now = time.time()
            if now - _last_analysis < _min_interval:
                continue
            _last_analysis = now

            lat = msg.get("lat", settings.default_lat)
            lng = msg.get("lng", settings.default_lng)
            location = msg.get("location", settings.fallback_address)
            source = msg.get("source", "webcam")

            result = await pipeline.process_frame_b64(frame_b64)

            response = {
                "type": "detection",
                "incident_type": result.incident_type,
                "priority": result.priority,
                "threat_level": result.threat_level,
                "confidence": result.confidence,
                "description": result.description,
                "detected_objects": [o.model_dump() for o in result.detected_objects],
                "scene_analysis": result.scene_analysis,
                "annotated_frame": result.annotated_frame_b64,
                "recommended_action": result.recommended_action,
                "hazard_type": result.hazard_type,
                "hazard_confirmed": result.hazard_confirmed,
            }
            await websocket.send_json(response)

            if result.hazard_confirmed and result.hazard_type:
                async with async_session() as db:
                    logged = await log_incident_tool(
                        {
                            "incident_type": result.incident_type,
                            "priority": result.priority,
                            "threat_level": result.threat_level,
                            "description": result.description,
                            "location": location,
                            "latitude": lat,
                            "longitude": lng,
                            "confidence": result.confidence,
                            "detected_objects": [o.model_dump() for o in result.detected_objects],
                            "scene_analysis": json.dumps(result.scene_analysis),
                            "recommended_action": result.recommended_action,
                            "source": source,
                        },
                        db,
                    )
                    await websocket.send_json(
                        {
                            "type": "hazard_alert",
                            "incident_id": logged["id"],
                            "hazard_type": result.hazard_type,
                            "incident_type": result.incident_type,
                            "priority": result.priority,
                            "confidence": result.confidence,
                            "description": result.description,
                            "timestamp": time.time(),
                            "snapshot_b64": result.annotated_frame_b64,
                            "location": location,
                            "latitude": lat,
                            "longitude": lng,
                        }
                    )

    except WebSocketDisconnect:
        pass
