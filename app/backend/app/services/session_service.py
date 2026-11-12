"""Lifecycle and isolation rules for anonymous page sessions."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.session import SessionModel
from app.models.voice_record import VoiceRecordModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_session(db: Session) -> SessionModel:
    session = SessionModel()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def require_active_session(session_id: str, db: Session) -> SessionModel:
    session = (
        db.query(SessionModel)
        .filter(SessionModel.id == session_id, SessionModel.is_closed.is_(False))
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Активная сессия не найдена")
    session.last_seen_at = utc_now()
    db.commit()
    return session


def close_session(session_id: str, db: Session) -> int:
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if session.is_closed:
        return 0

    now = utc_now()
    deleted_records = (
        db.query(VoiceRecordModel)
        .filter(
            VoiceRecordModel.session_id == session_id,
            VoiceRecordModel.is_deleted.is_(False),
        )
        .update(
            {VoiceRecordModel.is_deleted: True, VoiceRecordModel.deleted_at: now},
            synchronize_session=False,
        )
    )
    session.is_closed = True
    session.closed_at = now
    session.last_seen_at = now
    db.commit()
    return deleted_records
