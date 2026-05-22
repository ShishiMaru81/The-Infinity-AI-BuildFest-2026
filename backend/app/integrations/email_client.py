"""SMTP email with JPEG attachment."""

import asyncio
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app.config import settings


def _send_sync(
    to_addr: str,
    subject: str,
    body: str,
    attachment_path: Path | None,
) -> dict:
    if not settings.smtp_host or not settings.smtp_user:
        return {"status": "skipped", "reason": "SMTP not configured"}

    msg = MIMEMultipart()
    msg["From"] = settings.sender_email or settings.smtp_user
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if attachment_path and attachment_path.exists():
        with attachment_path.open("rb") as f:
            part = MIMEApplication(f.read(), _subtype="jpeg")
        part.add_header("Content-Disposition", "attachment", filename=attachment_path.name)
        msg.attach(part)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(msg["From"], [to_addr], msg.as_string())
        return {"status": "sent", "to": to_addr}
    except Exception as e:
        return {"status": "failed", "error": str(e), "to": to_addr}


async def send_email(
    to_addr: str,
    subject: str,
    body: str,
    attachment_path: Path | None = None,
) -> dict:
    return await asyncio.to_thread(_send_sync, to_addr, subject, body, attachment_path)
