"""Business logic for processing and querying voice messages."""

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.session import SessionModel
from app.models.voice_record import VoiceRecordModel
from app.services.sentiment_service import predict_sentiment
from app.services.transcription_service import transcribe_audio
from app.services.translation_service import translate_to_english


def process_voice_record(
    *,
    audio_path: Path,
    filename: str,
    content_type: str | None,
    browser_session: SessionModel,
    db: Session,
) -> VoiceRecordModel:
    transcript, detected_language = transcribe_audio(audio_path)
    analysis_text = translate_to_english(transcript)
    label, score, confidence = predict_sentiment(analysis_text)

    # The page may be closed while the relatively slow ML pipeline is running.
    db.refresh(browser_session)
    if browser_session.is_closed:
        raise RuntimeError("Сессия была закрыта во время обработки")

    record = VoiceRecordModel(
        session_id=browser_session.id,
        original_filename=filename,
        content_type=content_type,
        transcript=transcript,
        detected_language=detected_language,
        sentiment_label=label,
        sentiment_score=score,
        model_confidence=confidence,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    # Covers the race where close happened between the check and INSERT.
    db.refresh(browser_session)
    db.refresh(record)
    if browser_session.is_closed and not record.is_deleted:
        record.is_deleted = True
        record.deleted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
    return record


def list_session_records(session_id: str, db: Session) -> list[VoiceRecordModel]:
    return (
        db.query(VoiceRecordModel)
        .filter(
            VoiceRecordModel.session_id == session_id,
            VoiceRecordModel.is_deleted.is_(False),
        )
        .order_by(VoiceRecordModel.created_at.desc())
        .all()
    )


def get_session_record(record_id: int, session_id: str, db: Session) -> VoiceRecordModel | None:
    return (
        db.query(VoiceRecordModel)
        .filter(
            VoiceRecordModel.id == record_id,
            VoiceRecordModel.session_id == session_id,
            VoiceRecordModel.is_deleted.is_(False),
        )
        .first()
    )
