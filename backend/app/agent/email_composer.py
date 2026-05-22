"""LLM-generated emergency email body."""

import json

from app.config import settings


async def compose_email_body(
    *,
    threat_type: str,
    confidence: float,
    timestamp: str,
    location: str,
    description: str,
    reporter_name: str,
    reporter_phone: str,
) -> tuple[str, str]:
    subject = f"URGENT: Possible {threat_type} detected — automated alert"
    disclaimer = (
        "DISCLAIMER: This is an automated alert from the GuardianAI hazard detection system. "
        "Verify on scene before dispatching units. False reports to 999 may be prosecuted under Bangladesh law."
    )

    if settings.anthropic_api_key:
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=settings.anthropic_api_key)
            prompt = f"""Write a concise professional emergency email to Bangladesh National Emergency Service (999).
Include: detected object ({threat_type}), confidence ({confidence:.0%}), time ({timestamp}), location ({location}),
brief scene note ({description}), reporter ({reporter_name}, {reporter_phone}).
End with the automated disclaimer. Plain text only, no markdown."""

            msg = client.messages.create(
                model=settings.claude_model,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            body = msg.content[0].text.strip()
            if disclaimer not in body:
                body += f"\n\n{disclaimer}"
            return subject, body
        except Exception:
            pass

    body = (
        f"Automated Hazard Alert — GuardianAI\n\n"
        f"Detected threat: {threat_type}\n"
        f"Confidence: {confidence:.1%}\n"
        f"Timestamp (UTC): {timestamp}\n"
        f"Location: {location}\n"
        f"Scene: {description}\n\n"
        f"Reporter: {reporter_name}\n"
        f"Contact: {reporter_phone}\n\n"
        f"{disclaimer}"
    )
    return subject, body
