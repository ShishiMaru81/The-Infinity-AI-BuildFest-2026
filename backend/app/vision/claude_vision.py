import json
import re

from anthropic import Anthropic

from app.config import settings

SYSTEM_PROMPT = """You are a public safety AI. Analyze this CCTV/surveillance frame. Identify:
1) What is happening,
2) Threat level (SAFE / SUSPICIOUS / DANGER / CRITICAL),
3) Incident type (violence, weapon, accident, fire, normal),
4) Recommended action (none / alert_police / alert_hospital / alert_both).
Respond in JSON only with keys: happening, threat_level, incident_type, recommended_action, description."""


class ClaudeVisionAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None

    async def analyze(self, frame_b64: str, yolo_summary: str = "") -> dict:
        if not self.client:
            return self._mock_analysis(yolo_summary)

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

        try:
            msg = self.client.messages.create(
                model=settings.claude_model,
                max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            text = msg.content[0].text
            return self._parse_json(text)
        except Exception as e:
            return {
                "happening": "Analysis unavailable",
                "threat_level": "SUSPICIOUS",
                "incident_type": "normal",
                "recommended_action": "none",
                "description": str(e),
            }

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
        if "car" in low or "truck" in low:
            return {
                "happening": "Vehicle activity in surveillance zone",
                "threat_level": "SUSPICIOUS",
                "incident_type": "accident",
                "recommended_action": "alert_hospital",
                "description": "Possible traffic incident.",
            }
        return {
            "happening": "Routine surveillance activity",
            "threat_level": "SAFE",
            "incident_type": "normal",
            "recommended_action": "none",
            "description": "No immediate threat detected.",
        }
