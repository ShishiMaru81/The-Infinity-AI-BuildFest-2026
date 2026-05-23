from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM (Groq preferred when key set)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # Legacy alert mode (mock prints to console for Twilio helpers)
    alert_mode: str = "mock"
    police_number: str = "999"
    test_phone: str = ""

    # App safety mode: test (default) | real
    app_mode: str = "test"
    test_email: str = ""
    emergency_email: str = "999@police.gov.bd"
    real_dispatch_cooldown_sec: int = 300

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    sender_email: str = ""

    # Reporter / location fallback
    reporter_name: str = "GuardianAI Operator"
    reporter_phone: str = ""
    fallback_address: str = "Dhaka, Bangladesh"
    default_lat: float = 23.8103
    default_lng: float = 90.4125

    # Detection
    database_url: str = "sqlite+aiosqlite:///./guardianai.db"
    frame_fps: int = 8
    yolo_model: str = "yolov8n.pt"
    yolo_inference_conf: float = 0.15
    detection_confidence_threshold: float = 0.35
    detection_consecutive_frames: int = 3

    # Roboflow (optional — improves gun/fire/lighter)
    roboflow_api_key: str = ""
    roboflow_weapon_model: str = ""
    roboflow_fire_model: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
