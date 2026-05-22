from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_type: Mapped[str] = mapped_column(String(64))
    priority: Mapped[str] = mapped_column(String(32))
    threat_level: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    alert_status: Mapped[str] = mapped_column(String(32), default="PENDING")
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(256), default="Dhaka, Bangladesh")
    latitude: Mapped[float] = mapped_column(Float, default=23.8103)
    longitude: Mapped[float] = mapped_column(Float, default=90.4125)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    detected_objects: Mapped[str] = mapped_column(Text, default="[]")
    scene_analysis: Mapped[str] = mapped_column(Text, default="")
    recommended_action: Mapped[str] = mapped_column(String(64), default="none")
    agent_reasoning: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(64), default="webcam")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SettingsRow(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), unique=True)
    value: Mapped[str] = mapped_column(Text)
