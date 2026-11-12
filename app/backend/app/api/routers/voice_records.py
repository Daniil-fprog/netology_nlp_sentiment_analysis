import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import active_session_dependency
from app.core.config import MAX_AUDIO_SIZE_MB
from app.db.database import get_db
from app.models.session import SessionModel
from app.schemas.voice import VoiceRecordOut
from app.services.voice_record_service import (
    get_session_record,
    list_session_records,
    process_voice_record,
)


router = APIRouter(prefix="/api/records", tags=["voice records"])
ALLOWED_EXTENSIONS = {".ogg", ".oga", ".opus", ".mp3", ".wav", ".m4a", ".webm", ".mp4"}
ALLOWED_CONTENT_TYPES = {
    "audio/ogg", "audio/opus", "audio/mpeg", "audio/mp3", "audio/wav",
    "audio/x-wav", "audio/mp4", "audio/x-m4a", "audio/webm", "video/mp4",
    "application/ogg",
}


@router.get("", response_model=list[VoiceRecordOut])
def get_records(
    browser_session: SessionModel = Depends(active_session_dependency),
    db: Session = Depends(get_db),
):
    return list_session_records(browser_session.id, db)


@router.get("/{record_id}", response_model=VoiceRecordOut)
def get_record(
    record_id: int,
    browser_session: SessionModel = Depends(active_session_dependency),
    db: Session = Depends(get_db),
):
    record = get_session_record(record_id, browser_session.id, db)
    if record is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return record


@router.post("", response_model=VoiceRecordOut, status_code=status.HTTP_201_CREATED)
async def upload_record(
    audio: UploadFile = File(...),
    browser_session: SessionModel = Depends(active_session_dependency),
    db: Session = Depends(get_db),
):
    filename = Path(audio.filename or "voice.ogg").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Неподдерживаемый формат аудио")
    if audio.content_type and audio.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Неподдерживаемый MIME-тип аудио")

    max_bytes = MAX_AUDIO_SIZE_MB * 1024 * 1024
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = Path(temp_file.name)
            size = 0
            while chunk := await audio.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Файл больше {MAX_AUDIO_SIZE_MB} МБ",
                    )
                temp_file.write(chunk)
        if size == 0:
            raise HTTPException(status_code=422, detail="Аудиофайл пуст")

        try:
            return await run_in_threadpool(
                process_voice_record,
                audio_path=temp_path,
                filename=filename,
                content_type=audio.content_type,
                browser_session=browser_session,
                db=db,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        await audio.close()
        if temp_path is not None:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
