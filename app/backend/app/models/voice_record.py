"""Transcription and sentiment result produced from one voice file."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VoiceRecordModel(Base):
    __tablename__ = "voice_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    transcript = Column(Text, nullable=False)
    detected_language = Column(String(16), nullable=True)
    sentiment_label = Column(String(16), nullable=False)
    sentiment_score = Column(Float, nullable=False)
    model_confidence = Column(Float, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("SessionModel", back_populates="records")
