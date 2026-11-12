"""FastAPI application for session-scoped voice sentiment analysis."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 - registers SQLAlchemy models
from app.api.routers import sessions, voice_records
from app.core.config import CORS_ALLOWED_ORIGINS
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Voice Sentiment API",
    description="Расшифровка голосовых сообщений и бинарный анализ тональности.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Session-ID"],
)


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok"}


app.include_router(sessions.router)
app.include_router(voice_records.router)
