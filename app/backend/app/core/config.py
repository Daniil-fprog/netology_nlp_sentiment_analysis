"""Application settings read from environment variables."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'db_store' / 'sentiment.db'}",
)
SENTIMENT_MODEL_PATH = Path(
    os.getenv(
        "SENTIMENT_MODEL_PATH",
        str(BASE_DIR / "train_model" / "models" / "sentiment_model.joblib"),
    )
)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ru") or None
MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))
TRANSLATION_MODEL_NAME = os.getenv(
    "TRANSLATION_MODEL_NAME", "Helsinki-NLP/opus-mt-ru-en"
)

DEFAULT_CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        ",".join(DEFAULT_CORS_ALLOWED_ORIGINS),
    ).split(",")
    if origin.strip()
]
