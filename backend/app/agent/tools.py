import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Incident, SettingsRow
from app.services.alerts import format_alert_message, make_emergency_call, send_sms_alert
from app.services.hospitals import get_nearest_hospital, HOSPITALS

# WebSocket broadcast registry (set from websocket module)
dashboard_connections: list = []


async def get_incident_details(incident_id: int, db: AsyncSession) -> dict:
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        return {"error": "Incident not found"}
    return {
        "id": inc.id,
        "incident_type": inc.incident_type,
        "priority": inc.priority,
        "threat_level": inc.threat_level,
        "description": inc.description,
        "location": inc.location,
        "latitude": inc.latitude,
        "longitude": inc.longitude,
        "confidence": inc.confidence,
        "alert_status": inc.alert_status,
        "recommended_action": inc.recommended_action,
    }


async def get_nearest_hospital_tool(lat: float, lng: float, db: AsyncSession) -> dict:
    custom = await _load_hospitals(db)
    return get_nearest_hospital(lat, lng, custom)


async def send_sms_alert_tool(number: str, message: str) -> dict:
    return await send_sms_alert(number, message)


async def make_emergency_call_tool(number: str, message: str) -> dict:
    return await make_emergency_call(number, message)


async def log_incident_tool(incident_data: dict, db: AsyncSession) -> dict:
    inc = Incident(
        incident_type=incident_data.get("incident_type", "NORMAL"),
        priority=incident_data.get("priority", "LOW"),
        threat_level=incident_data.get("threat_level", "SAFE"),
        description=incident_data.get("description", ""),
        location=incident_data.get("location", "Dhaka, Bangladesh"),
        latitude=incident_data.get("latitude", settings.default_lat),
        longitude=incident_data.get("longitude", settings.default_lng),
        confidence=incident_data.get("confidence", 0.0),
        detected_objects=json.dumps(incident_data.get("detected_objects", [])),
        scene_analysis=incident_data.get("scene_analysis", ""),
        recommended_action=incident_data.get("recommended_action", "none"),
        source=incident_data.get("source", "webcam"),
        status="LOGGED",
        alert_status="PENDING",
    )
    db.add(inc)
    await db.commit()
    await db.refresh(inc)
    return {"id": inc.id, "status": "logged"}


async def notify_dashboard_tool(incident_id: int, payload: dict) -> dict:
    message = {"type": "incident_alert", "incident_id": incident_id, **payload}
    dead = []
    for ws in dashboard_connections:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in dashboard_connections:
            dashboard_connections.remove(ws)
    return {"notified": len(dashboard_connections)}


async def _load_hospitals(db: AsyncSession) -> list | None:
    result = await db.execute(
        select(SettingsRow).where(SettingsRow.key == "hospitals")
    )
    row = result.scalar_one_or_none()
    if row:
        return json.loads(row.value)
    return None


async def update_incident_alert_status(
    incident_id: int, alert_status: str, agent_reasoning: str, db: AsyncSession
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = result.scalar_one_or_none()
    if inc:
        inc.alert_status = alert_status
        inc.agent_reasoning = agent_reasoning
        inc.status = "RESPONDED" if alert_status == "SENT" else inc.status
        await db.commit()
