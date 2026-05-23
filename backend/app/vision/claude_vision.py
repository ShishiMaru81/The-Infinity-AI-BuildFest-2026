import json
import re

from app.config import settings
from app.integrations.groq_llm import groq_available, groq_chat

SYSTEM_PROMPT = """You are a public safety AI analyzing surveillance detections.
Respond in JSON only with keys: happening, threat_level, incident_type, recommended_action, description.
threat_level: SAFE | SUSPICIOUS | DANGER | CRITICAL
incident_type: violence | weapon | accident | fire | normal
recommended_action: none | alert_police | alert_hospital | alert_both"""


class ClaudeVisionAnalyzer:
    """Scene analysis — prefers Groq (text from YOLO), then Anthropic vision, then rules."""

    def __init__(self):
        self._anthropic = None
        if settings.anthropic_api_key:
            try:
                from anthropic import Anthropic

                self._anthropic = Anthropic(api_key=settings.anthropic_api_key)
            except Exception:
                pass

    async def analyze(self, frame_b64: str, yolo_summary: str = "") -> dict:
        if groq_available():
            text = await groq_chat(
                SYSTEM_PROMPT,
                f"YOLO detections: {yolo_summary}. Analyze threat for Bangladesh public safety.",
                max_tokens=400,
            )
            if text:
                parsed = self._parse_json(text)
                if parsed.get("threat_level"):
                    return parsed

        if self._anthropic:
            try:
                user_content = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": frame_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"YOLO detections: {yolo_summary}. Analyze this frame.",
                    },
                ]
                msg = self._anthropic.messages.create(
                    model=settings.claude_model,
                    max_tokens=512,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_content}],
                )
                return self._parse_json(msg.content[0].text)
            except Exception as e:
                return {
                    "happening": "Analysis unavailable",
                    "threat_level": "SUSPICIOUS",
                    "incident_type": "normal",
                    "recommended_action": "none",
                    "description": str(e),
                }

        return self._mock_analysis(yolo_summary)

    def _parse_json(self, text: str) -> dict:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {
            "happening": text[:200],
            "threat_level": "SUSPICIOUS",
            "incident_type": "normal",
            "recommended_action": "none",
            "description": text,
        }

    def _mock_analysis(self, yolo_summary: str) -> dict:
        low = yolo_summary.lower()
        if "knife" in low or "bat" in low or "gun" in low or "weapon" in low:
            return {
                "happening": "Possible weapon visible in frame",
                "threat_level": "CRITICAL",
                "incident_type": "weapon",
                "recommended_action": "alert_police",
                "description": "Weapon-like object detected by vision pipeline.",
            }
        if "fire" in low:
            return {
                "happening": "Fire or smoke detected",
                "threat_level": "CRITICAL",
                "incident_type": "fire",
                "recommended_action": "alert_both",
                "description": "Fire incident requires emergency response.",
            }
        return {
            "happening": "Routine surveillance activity",
            "threat_level": "SAFE",
            "incident_type": "normal",
            "recommended_action": "none",
            "description": "No immediate threat detected.",
        }
