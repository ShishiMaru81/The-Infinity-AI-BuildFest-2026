"""Append-only dispatch event log (dispatch_log.json)."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[2] / "dispatch_log.json"


def _ensure_file() -> None:
    if not LOG_PATH.exists():
        LOG_PATH.write_text("[]", encoding="utf-8")


def append_event(
    *,
    threat_type: str,
    confidence: float,
    snapshot_path: str,
    email_status: str,
    call_status: str,
    sms_status: str,
    mode: str,
    extra: dict | None = None,
) -> dict:
    _ensure_file()
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "threat_type": threat_type,
        "confidence": confidence,
        "snapshot_path": snapshot_path,
        "email_status": email_status,
        "call_status": call_status,
        "sms_status": sms_status,
        "mode": mode,
        **(extra or {}),
    }
    try:
        data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = []
    data.append(entry)
    LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return entry


def list_events(limit: int = 50) -> list[dict]:
    _ensure_file()
    try:
        data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return list(reversed(data[-limit:]))
