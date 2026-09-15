"""
Sessions router.
POST /api/sessions           – create session
GET  /api/sessions/{id}      – get session metadata (404 or expired info)
DELETE /api/sessions/{id}    – soft-delete (mark expired)
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models import Session as SessionModel

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
settings = get_settings()


class SessionCreate(BaseModel):
    title: str | None = None


class SessionResponse(BaseModel):
    id: str
    title: str | None
    created_at: datetime
    expires_at: datetime
    is_expired: bool
    document_count: int

    model_config = {"from_attributes": True}


def _to_response(session: SessionModel) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        expires_at=session.expires_at,
        is_expired=session.is_expired,
        document_count=len(session.documents),
    )


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreate = SessionCreate(),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Create a new session."""
    now = datetime.now(UTC)
    session = SessionModel(
        title=body.title,
        created_at=now,
        expires_at=now + timedelta(hours=settings.session_ttl_hours),
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return _to_response(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Get session metadata. Returns 404 if not found, 410 if expired/deleted."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.is_expired:
        raise HTTPException(status_code=410, detail="Session has expired or been deleted.")

    return _to_response(session)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a session (marks it as expired)."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    session.deleted_at = datetime.now(UTC)
    await db.flush()
