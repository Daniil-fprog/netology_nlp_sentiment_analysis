from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.session import SessionModel
from app.services.session_service import require_active_session


def active_session_dependency(
    x_session_id: str = Header(..., alias="X-Session-ID"),
    db: Session = Depends(get_db),
) -> SessionModel:
    return require_active_session(x_session_id, db)
