"""Speech-to-text service backed by faster-whisper."""

from functools import lru_cache
from pathlib import Path

from app.core.config import (
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_LANGUAGE,
    WHISPER_MODEL_SIZE,
)


@lru_cache(maxsize=1)
def get_whisper_model():
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Не установлен пакет faster-whisper") from exc

    return WhisperModel(
        WHISPER_MODEL_SIZE,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE,
    )


def transcribe_audio(path: Path) -> tuple[str, str | None]:
    model = get_whisper_model()
    segments, info = model.transcribe(
        str(path), language=WHISPER_LANGUAGE, vad_filter=True, beam_size=5
    )
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    if not transcript:
        raise ValueError("В аудио не удалось распознать речь")
    return transcript, getattr(info, "language", WHISPER_LANGUAGE)
