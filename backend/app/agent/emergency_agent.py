import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import tools
from app.config import settings
from app.services.alerts import format_alert_message

AGENT_PROMPT = """You are GuardianAI Emergency Response Agent for Bangladesh.
Given an incident, decide and execute the correct emergency response using available tools.
Bangladesh unified emergency number is 999 (Police, Fire, Ambulance).
For accidents, contact nearest hospital. For weapons/violence/fire, contact 999 immediately.
Always: log reasoning, send alerts, notify dashboard."""


class EmergencyResponseAgent:
    """Rule-based agent with optional LangChain enhancement when API key present."""

    async def respond(self, incident_id: int, incident_data: dict, db: AsyncSession) -> str:
        itype = incident_data.get("incident_type", "NORMAL")
        lat = incident_data.get("latitude", settings.default_lat)
        lng = incident_data.get("longitude", settings.default_lng)
        location = incident_data.get("location", "Dhaka, Bangladesh")
        confidence = incident_data.get("confidence", 0.0)
        description = incident_data.get("description", "")
        ts = datetime.utcnow().isoformat()

        reasoning_steps = []
        alert_results = []

        msg = format_alert_message(itype, location, ts, confidence, description)

        if itype in ("WEAPON_DETECTED", "VIOLENCE", "FIRE"):
            reasoning_steps.append(
                f"CRITICAL: {itype} near {location} → Contacting Bangladesh emergency 999 immediately."
            )
            sms = await tools.send_sms_alert_tool(settings.police_number, msg)
            call = await tools.make_emergency_call_tool(settings.police_number, msg)
            alert_results.extend([sms, call])
            if itype == "FIRE":
                reasoning_steps.append("Fire detected → Police and fire services notified via 999.")

        elif itype == "ACCIDENT":
            hospital = await tools.get_nearest_hospital_tool(lat, lng, db)
            reasoning_steps.append(
                f"Accident at {location} → Nearest hospital: {hospital['name']} ({hospital['distance_km']} km)."
            )
            sms = await tools.send_sms_alert_tool(hospital["phone"], msg)
            alert_results.append(sms)

        elif itype == "SUSPICIOUS_ACTIVITY":
            reasoning_steps.append("Suspicious activity logged for dashboard review. No emergency call.")
        else:
            reasoning_steps.append("Normal activity — no alert required.")

        reasoning = " ".join(reasoning_steps)
        await tools.update_incident_alert_status(
            incident_id,
            "SENT" if alert_results else "PENDING",
            reasoning,
            db,
        )

        await tools.notify_dashboard_tool(
            incident_id,
            {
                "incident_type": itype,
                "priority": incident_data.get("priority"),
                "alert_status": "SENT" if alert_results else "PENDING",
                "agent_message": "Agent is contacting 999..." if itype in ("WEAPON_DETECTED", "VIOLENCE", "FIRE") else "Agent notified nearest hospital.",
                "reasoning": reasoning,
            },
        )

        # Try LangChain for richer reasoning when key available
        if settings.anthropic_api_key:
            try:
                extra = await self._langchain_reasoning(incident_data, reasoning)
                if extra:
                    reasoning += f" | AI: {extra}"
            except Exception:
                pass

        return reasoning

    async def _langchain_reasoning(self, incident_data: dict, base: str) -> str:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatAnthropic(
            model=settings.claude_model,
            api_key=settings.anthropic_api_key,
            max_tokens=256,
        )
        resp = await llm.ainvoke(
            [
                SystemMessage(content=AGENT_PROMPT),
                HumanMessage(
                    content=f"Incident: {json.dumps(incident_data)}. Prior actions: {base}. Summarize response in one sentence."
                ),
            ]
        )
        return resp.content if hasattr(resp, "content") else str(resp)
