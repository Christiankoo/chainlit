# api_sessions.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.db.models import Session as SessionModel

router_crud = APIRouter(prefix="/api/sessions", tags=["sessions"])

class SessionOut(BaseModel):
    id: UUID
    user_id: str
    title: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SessionCreate(BaseModel):
    user_id: str
    title: str | None = None

class SessionUpdate(BaseModel):
    title: str | None = None

@router_crud.get("", response_model=list[SessionOut])
def get_sessions(
    user_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(SessionModel)
    if user_id:
        q = q.filter(SessionModel.user_id == user_id)

    rows = (
        q.order_by(SessionModel.created_at.desc())
         .offset(offset)
         .limit(min(limit, 200))   # simple safety cap
         .all()
    )
    return rows

def create_session_record(
    db: Session,
    *,
    user_id: str,
    title: str | None = None,
) -> SessionModel:
    obj = SessionModel(user_id=user_id, title=title)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router_crud.post("", response_model=SessionOut)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    return create_session_record(
        db,
        user_id=payload.user_id,
        title=payload.title,
    )

def update_session_record(
    db: Session,
    *,
    session_id: UUID,
    title: str | None = None,
) -> SessionModel:
    obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Only update fields that were provided (patch semantics)
    if title is not None:
        obj.title = title

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router_crud.patch("/{session_id}", response_model=SessionOut)
def update_session(session_id: UUID, payload: SessionUpdate, db: Session = Depends(get_db)):
    return update_session_record(
        db,
        session_id=session_id,
        title=payload.title,
    )

def delete_session_record(db: Session, *, session_id: UUID) -> None:
    obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    db.delete(obj)
    db.commit()


@router_crud.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    delete_session_record(db, session_id=session_id)
    return None