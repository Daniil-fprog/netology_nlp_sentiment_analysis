"""Integration tests for the session-scoped API described in the assignment."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app
from app.models.voice_record import VoiceRecordModel
import app.services.voice_record_service as record_service


@pytest.fixture()
def database(tmp_path: Path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)
    try:
        yield session_factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(database, monkeypatch):
    def override_db():
        db = database()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(
        record_service, "transcribe_audio", lambda _: ("Сегодня отличный день", "ru")
    )
    monkeypatch.setattr(
        record_service, "translate_to_english", lambda _: "Today is a wonderful day"
    )
    monkeypatch.setattr(
        record_service, "predict_sentiment", lambda _: ("positive", 91.5, 91.5)
    )
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def start_session(client: TestClient) -> str:
    response = client.post("/api/sessions")
    assert response.status_code == 201
    return response.json()["id"]


def test_voice_record_is_visible_only_inside_its_session(client: TestClient):
    first_session = start_session(client)
    second_session = start_session(client)

    created = client.post(
        "/api/records",
        headers={"X-Session-ID": first_session},
        files={"audio": ("telegram.ogg", b"fake-audio", "audio/ogg")},
    )
    assert created.status_code == 201
    record = created.json()
    assert record["transcript"] == "Сегодня отличный день"
    assert record["sentiment_label"] == "positive"

    own_records = client.get(
        "/api/records", headers={"X-Session-ID": first_session}
    )
    assert own_records.status_code == 200
    assert [item["id"] for item in own_records.json()] == [record["id"]]

    foreign_records = client.get(
        "/api/records", headers={"X-Session-ID": second_session}
    )
    assert foreign_records.status_code == 200
    assert foreign_records.json() == []

    foreign_record = client.get(
        f"/api/records/{record['id']}", headers={"X-Session-ID": second_session}
    )
    assert foreign_record.status_code == 404


def test_closing_session_soft_deletes_records(client: TestClient, database):
    session_id = start_session(client)
    created = client.post(
        "/api/records",
        headers={"X-Session-ID": session_id},
        files={"audio": ("voice.ogg", b"fake-audio", "audio/ogg")},
    )
    record_id = created.json()["id"]

    closed = client.post(f"/api/sessions/{session_id}/close")
    assert closed.status_code == 200
    assert closed.json()["deleted_records"] == 1

    unavailable = client.get("/api/records", headers={"X-Session-ID": session_id})
    assert unavailable.status_code == 404

    with database() as db:
        stored = db.query(VoiceRecordModel).filter_by(id=record_id).one()
        assert stored.is_deleted is True
        assert stored.deleted_at is not None


def test_upload_requires_session_and_supported_audio(client: TestClient):
    no_session = client.post(
        "/api/records", files={"audio": ("voice.ogg", b"audio", "audio/ogg")}
    )
    assert no_session.status_code == 422

    session_id = start_session(client)
    unsupported = client.post(
        "/api/records",
        headers={"X-Session-ID": session_id},
        files={"audio": ("note.txt", b"not audio", "text/plain")},
    )
    assert unsupported.status_code == 415


def test_close_is_idempotent(client: TestClient):
    session_id = start_session(client)
    assert client.post(f"/api/sessions/{session_id}/close").status_code == 200
    repeated = client.post(f"/api/sessions/{session_id}/close")
    assert repeated.status_code == 200
    assert repeated.json()["deleted_records"] == 0
