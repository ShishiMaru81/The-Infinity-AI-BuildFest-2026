"""Twilio SMS and voice with graceful skip when credentials missing."""

import logging

from app.config import settings
from app.services.alerts import format_alert_message, make_emergency_call, send_sms_alert

logger = logging.getLogger(__name__)


def twilio_configured() -> bool:
    return bool(
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_phone_number
    )


async def send_sms(number: str, message: str, *, test_mode: bool) -> dict:
    if test_mode:
        logger.info("[TEST MODE] SMS skipped -> %s: %s", number, message[:80])
        return {"status": "skipped_test_mode", "to": number}
    if not twilio_configured():
        logger.warning("Twilio not configured; skipping SMS to %s", number)
        return {"status": "skipped", "reason": "Twilio credentials missing", "to": number}
    try:
        return await send_sms_alert(number, message)
    except Exception as e:
        logger.exception("SMS failed")
        return {"status": "failed", "error": str(e), "to": number}


async def place_call(number: str, message: str, *, test_mode: bool) -> dict:
    if test_mode:
        logger.info("[TEST MODE] Call skipped -> %s", number)
        return {"status": "skipped_test_mode", "to": number}
    if not twilio_configured():
        logger.warning("Twilio not configured; skipping call to %s", number)
        return {"status": "skipped", "reason": "Twilio credentials missing", "to": number}
    try:
        return await make_emergency_call(number, message)
    except Exception as e:
        logger.exception("Call failed")
        return {"status": "failed", "error": str(e), "to": number}


def build_alert_message(
    threat_type: str,
    location: str,
    timestamp: str,
    confidence: float,
    description: str,
) -> str:
    return format_alert_message(
        f"HAZARD:{threat_type.upper()}",
        location,
        timestamp,
        confidence,
        description,
    )
