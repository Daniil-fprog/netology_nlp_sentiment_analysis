from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.voice import SessionClosedOut, SessionOut
from app.services.session_service import close_session, create_session


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def start_session(db: Session = Depends(get_db)):
    return create_session(db)


@router.post("/{session_id}/close", response_model=SessionClosedOut)
def finish_session(session_id: str, db: Session = Depends(get_db)):
    deleted_records = close_session(session_id, db)
    return SessionClosedOut(session_id=session_id, deleted_records=deleted_records)
