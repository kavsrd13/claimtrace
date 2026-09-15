"""
Documents router.
POST /api/sessions/{id}/documents  – upload a document (slot 0 or 1)
GET  /api/sessions/{id}/documents  – list documents in session
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models import Document
from models import Session as SessionModel
from services.comparator import build_embeddings, serialize_embeddings
from services.extractor import ExtractionError, extract_text
from services.security import SecurityError, check_session_active, validate_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["documents"])
settings = get_settings()


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    slot: int
    has_text: bool

    model_config = {"from_attributes": True}


def _to_response(doc: Document) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        content_type=doc.content_type,
        size_bytes=doc.size_bytes,
        uploaded_at=doc.uploaded_at,
        slot=doc.slot,
        has_text=bool(doc.extracted_text),
    )


async def _get_active_session(session_id: str, db: AsyncSession) -> SessionModel:
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    try:
        check_session_active(session.expires_at, session.deleted_at)
    except SecurityError as e:
        raise HTTPException(status_code=410, detail=str(e)) from e
    return session


@router.post("/{session_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    session_id: str,
    slot: int = Form(0, ge=0, le=1),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Upload a document into slot 0 (Doc A) or slot 1 (Doc B)."""
    await _get_active_session(session_id, db)

    content = await file.read()
    filename = file.filename or "upload"
    content_type = file.content_type or "application/octet-stream"

    # Security validation
    try:
        validate_upload(filename, content_type, len(content), settings.max_upload_size_bytes)
    except SecurityError as e:
        raise HTTPException(status_code=422, detail={"code": e.code, "message": str(e)}) from e

    # Text extraction
    try:
        chunks = extract_text(content, filename, content_type)
    except ExtractionError as e:
        raise HTTPException(
            status_code=422, detail={"code": "EXTRACTION_ERROR", "message": str(e)}
        ) from e

    full_text = "\n\n".join(c.text for c in chunks)

    # Embeddings (best-effort; skip if Azure OpenAI not configured)
    embeddings_json: str | None = None
    if settings.azure_openai_endpoint and settings.azure_openai_api_key:
        try:
            embeddings, valid_chunks = await build_embeddings(chunks)
            if embeddings:
                embeddings_json = serialize_embeddings(embeddings)
        except Exception as exc:
            logger.warning("Embedding failed, skipping: %s", exc)

    # Remove existing document in same slot
    existing = await db.execute(
        select(Document).where(Document.session_id == session_id, Document.slot == slot)
    )
    for old_doc in existing.scalars().all():
        await db.delete(old_doc)

    doc = Document(
        session_id=session_id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(content),
        extracted_text=full_text,
        slot=slot,
        embeddings_json=embeddings_json,
        uploaded_at=datetime.now(UTC),
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return _to_response(doc)


@router.get("/{session_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[DocumentResponse]:
    """List all documents in a session."""
    await _get_active_session(session_id, db)
    result = await db.execute(
        select(Document).where(Document.session_id == session_id).order_by(Document.slot)
    )
    docs = result.scalars().all()
    return [_to_response(d) for d in docs]
