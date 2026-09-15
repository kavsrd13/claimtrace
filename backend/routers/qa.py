"""
Q&A router.
POST /api/sessions/{id}/ask  – ask a question grounded in session documents
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models import Document
from models import Session as SessionModel
from services.comparator import deserialize_embeddings, retrieve_top_k
from services.extractor import _extract_txt  # noqa: PLC0415
from services.llm import QAResponse, answer_question, embed_texts
from services.security import SecurityError, check_prompt_injection, check_session_active

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["qa"])
settings = get_settings()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class CitationOut(BaseModel):
    source_label: str
    text: str
    score: float


class AskResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    is_supported: bool


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


@router.post("/{session_id}/ask", response_model=AskResponse)
async def ask_question_endpoint(
    session_id: str,
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
) -> AskResponse:
    """Answer a question grounded in the session's uploaded documents."""
    await _get_active_session(session_id, db)

    # Security: prompt injection check
    try:
        check_prompt_injection(body.question)
    except SecurityError as e:
        raise HTTPException(status_code=422, detail={"code": e.code, "message": str(e)}) from e

    # Fetch documents
    result = await db.execute(
        select(Document).where(Document.session_id == session_id).order_by(Document.slot)
    )
    docs = list(result.scalars().all())

    if not docs:
        raise HTTPException(status_code=422, detail="No documents uploaded in this session.")

    if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="Azure OpenAI is not configured.",
        )

    # Retrieve relevant chunks using embeddings
    all_chunks: list[dict] = []

    # Embed the query
    try:
        query_embeddings = await embed_texts([body.question])
        query_embedding = query_embeddings[0]
    except Exception as exc:
        logger.warning("Could not embed query: %s; falling back to full-text.", exc)
        query_embedding = None

    doc_labels = ["Doc A", "Doc B"]
    for doc in docs:
        label = doc_labels[doc.slot] if doc.slot < len(doc_labels) else f"Doc {doc.slot}"
        if query_embedding and doc.embeddings_json:
            try:
                embeddings = deserialize_embeddings(doc.embeddings_json)
                chunks = _extract_txt(doc.extracted_text.encode()) if doc.extracted_text else []
                top = retrieve_top_k(query_embedding, embeddings, chunks, label, k=4)
                all_chunks.extend(top)
            except Exception as exc:
                logger.warning("Retrieval failed for doc %s: %s", doc.id, exc)
                # Fall back to first N paragraphs
                _add_fallback_chunks(doc, label, all_chunks)
        else:
            _add_fallback_chunks(doc, label, all_chunks)

    # Sort by score and take top-8
    all_chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_chunks = all_chunks[:8]

    try:
        qa_result: QAResponse = await answer_question(body.question, top_chunks)
    except Exception as exc:
        logger.exception("Q&A failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Q&A failed: {exc}") from exc

    return AskResponse(
        answer=qa_result.answer,
        citations=[
            CitationOut(source_label=c.source_label, text=c.text, score=c.score)
            for c in qa_result.citations
        ],
        is_supported=qa_result.is_supported,
    )


def _add_fallback_chunks(doc: Document, label: str, out: list[dict]) -> None:
    """Add first few paragraphs as fallback chunks."""
    if not doc.extracted_text:
        return
    paragraphs = [p.strip() for p in doc.extracted_text.split("\n\n") if p.strip()]
    for i, para in enumerate(paragraphs[:4], start=1):
        out.append({"label": f"{label} · ¶{i}", "text": para, "score": 0.0})
