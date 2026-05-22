"""Orchestrate email + Twilio dispatch with test/real mode and cooldown."""

import base64
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.email_composer import compose_email_body
from app.agent.tools import notify_dashboard_tool, update_incident_alert_status
from app.config import settings
from app.integrations import email_client, twilio_client
from app.utils import cooldown, dispatch_log

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)


def resolve_mode(requested_mode: str | None) -> str:
    """test | real — default test."""
    mode = (requested_mode or settings.app_mode or "test").lower()
    return "real" if mode == "real" else "test"


def email_recipient(test_mode: bool) -> str:
    if test_mode:
        return settings.test_email or settings.smtp_user or "test@example.com"
    return settings.emergency_email


async def run_dispatch(
    *,
    incident_id: int | None,
    threat_type: str,
    confidence: float,
    location: str,
    latitude: float,
    longitude: float,
    description: str,
    snapshot_b64: str | None,
    requested_mode: str | None,
    db: AsyncSession,
) -> dict:
    test_mode = resolve_mode(requested_mode) == "test"

    if not test_mode:
        allowed, remaining = cooldown.can_dispatch_real(settings.real_dispatch_cooldown_sec)
        if not allowed:
            return {
                "status": "blocked",
                "reason": f"Real dispatch cooldown active. Try again in {remaining}s.",
                "cooldown_remaining_sec": remaining,
            }

    ts = datetime.now(timezone.utc).isoformat()
    snapshot_path = ""
    if snapshot_b64:
        snapshot_path = str(SNAPSHOT_DIR / f"{incident_id or 'adhoc'}_{int(datetime.now().timestamp())}.jpg")
        Path(snapshot_path).write_bytes(base64.b64decode(snapshot_b64))

    subject, body = await compose_email_body(
        threat_type=threat_type,
        confidence=confidence,
        timestamp=ts,
        location=location,
        description=description,
        reporter_name=settings.reporter_name,
        reporter_phone=settings.reporter_phone,
    )

    to_email = email_recipient(test_mode)
    email_result = await email_client.send_email(
        to_email,
        subject,
        body,
        Path(snapshot_path) if snapshot_path else None,
    )

    sms_msg = twilio_client.build_alert_message(
        threat_type, location, ts, confidence, description
    )
    call_number = settings.police_number if not test_mode else settings.test_phone or settings.police_number
    sms_result = await twilio_client.send_sms(call_number, sms_msg, test_mode=test_mode)
    call_result = await twilio_client.place_call(call_number, sms_msg, test_mode=test_mode)

    if not test_mode and email_result.get("status") == "sent":
        cooldown.record_real_dispatch()

    log_entry = dispatch_log.append_event(
        threat_type=threat_type,
        confidence=confidence,
        snapshot_path=snapshot_path,
        email_status=email_result.get("status", "unknown"),
        call_status=call_result.get("status", "unknown"),
        sms_status=sms_result.get("status", "unknown"),
        mode="test" if test_mode else "real",
        extra={
            "incident_id": incident_id,
            "email_to": to_email,
            "location": location,
        },
    )

    if incident_id:
        reasoning = (
            f"Dispatch ({'TEST' if test_mode else 'REAL'}): email={email_result.get('status')}, "
            f"sms={sms_result.get('status')}, call={call_result.get('status')}"
        )
        await update_incident_alert_status(
            incident_id,
            "SENT" if email_result.get("status") == "sent" else "PENDING",
            reasoning,
            db,
        )
        await notify_dashboard_tool(
            incident_id,
            {
                "incident_type": threat_type,
                "priority": "CRITICAL",
                "alert_status": "SENT" if email_result.get("status") == "sent" else "PENDING",
                "agent_message": "Dispatch completed",
                "dispatch_status": {
                    "email": email_result.get("status"),
                    "sms": sms_result.get("status"),
                    "call": call_result.get("status"),
                    "mode": "test" if test_mode else "real",
                },
            },
        )

    return {
        "status": "completed",
        "mode": "test" if test_mode else "real",
        "email": email_result,
        "sms": sms_result,
        "call": call_result,
        "log_id": log_entry["id"],
        "email_to": to_email,
    }
