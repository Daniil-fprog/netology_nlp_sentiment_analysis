"""Anonymous browser session model."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    is_closed = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    records = relationship(
        "VoiceRecordModel", back_populates="session", cascade="all, delete-orphan"
    )
