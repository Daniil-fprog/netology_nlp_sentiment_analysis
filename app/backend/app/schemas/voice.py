"""Public API contracts for sessions and voice records."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionOut(BaseModel):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoiceRecordOut(BaseModel):
    id: int
    original_filename: str
    transcript: str
    detected_language: str | None
    sentiment_label: str
    sentiment_score: float
    model_confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionClosedOut(BaseModel):
    session_id: str
    deleted_records: int
