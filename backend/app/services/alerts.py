from app.config import settings


def format_alert_message(
    incident_type: str,
    location: str,
    timestamp: str,
    confidence: float,
    description: str,
) -> str:
    return (
        f"GUARDIAN AI ALERT - {incident_type} detected at {location}/{timestamp}. "
        f"Confidence: {confidence:.0%}. Description: {description}. "
        "Please respond immediately."
    )


async def send_sms_alert(number: str, message: str) -> dict:
    if settings.alert_mode == "mock":
        print(f"[MOCK SMS] To: {number}\n{message}")
        return {"status": "mock_sent", "to": number, "message": message}

    from twilio.rest import Client

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    msg = client.messages.create(
        body=message,
        from_=settings.twilio_phone_number,
        to=number,
    )
    return {"status": "sent", "sid": msg.sid}


async def make_emergency_call(number: str, message: str) -> dict:
    if settings.alert_mode == "mock":
        print(f"[MOCK CALL] To: {number}\n{message}")
        return {"status": "mock_called", "to": number}

    from twilio.rest import Client
    from twilio.twiml.voice_response import VoiceResponse

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    twiml = VoiceResponse()
    twiml.say(message, language="en-US")
    call = client.calls.create(
        twiml=str(twiml),
        to=number,
        from_=settings.twilio_phone_number,
    )
    return {"status": "called", "sid": call.sid}
