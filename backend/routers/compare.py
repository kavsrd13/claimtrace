"""
Comparison router.
POST /api/sessions/{id}/compare  – compare the two uploaded documents
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models import Document
from models import Session as SessionModel
from services.comparator import compare_two_documents
from services.security import SecurityError, check_session_active

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["compare"])
settings = get_settings()


class DifferenceItem(BaseModel):
    aspect: str
    doc_a: str
    doc_b: str


class ClaimItem(BaseModel):
    id: str
    claim: str
    source_a: str | None
    source_b: str | None
    verdict: str  # agree | disagree | only_in_a | only_in_b


class CompareResponse(BaseModel):
    summary: str
    similarities: list[str]
    differences: list[DifferenceItem]
    claims: list[ClaimItem]
    doc_a_name: str
    doc_b_name: str


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


@router.post("/{session_id}/compare", response_model=CompareResponse)
async def compare_documents(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> CompareResponse:
    """Compare the two documents in a session using Azure OpenAI."""
    await _get_active_session(session_id, db)

    result = await db.execute(
        select(Document).where(Document.session_id == session_id).order_by(Document.slot)
    )
    docs = result.scalars().all()

    doc_map = {d.slot: d for d in docs}
    if 0 not in doc_map or 1 not in doc_map:
        raise HTTPException(
            status_code=422,
            detail="Both documents must be uploaded before comparing. Upload slot 0 (Doc A) and slot 1 (Doc B).",
        )

    doc_a = doc_map[0]
    doc_b = doc_map[1]

    if not doc_a.extracted_text or not doc_b.extracted_text:
        raise HTTPException(status_code=422, detail="Document text could not be extracted.")

    if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY.",
        )

    try:
        # Re-parse text into chunks for the comparator
        from services.extractor import _extract_txt  # noqa: PLC0415

        chunks_a = _extract_txt(doc_a.extracted_text.encode())
        chunks_b = _extract_txt(doc_b.extracted_text.encode())
        result_data = await compare_two_documents(
            chunks_a, chunks_b, doc_a.filename, doc_b.filename
        )
    except Exception as exc:
        logger.exception("Comparison failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Comparison failed: {exc}") from exc

    # Resilient normalization of LLM response fields
    raw_summary = result_data.get("summary", "")
    if isinstance(raw_summary, list):
        summary_str = "\n\n".join(str(s) for s in raw_summary)
    else:
        summary_str = str(raw_summary) if raw_summary else ""

    raw_similarities = result_data.get("similarities", [])
    similarities_list = [str(s) for s in raw_similarities] if isinstance(raw_similarities, list) else []

    differences_list = []
    for d in result_data.get("differences", []):
        if isinstance(d, dict):
            differences_list.append(
                DifferenceItem(
                    aspect=d.get("aspect", "General"),
                    doc_a=d.get("doc_a", ""),
                    doc_b=d.get("doc_b", ""),
                )
            )
        elif isinstance(d, str):
            differences_list.append(
                DifferenceItem(aspect="Comparison", doc_a=d, doc_b="")
            )

    claims_list = []
    for i, c in enumerate(result_data.get("claims", []), start=1):
        if isinstance(c, dict):
            claims_list.append(
                ClaimItem(
                    id=c.get("id", f"C{i:03d}"),
                    claim=c.get("claim", ""),
                    source_a=c.get("source_a"),
                    source_b=c.get("source_b"),
                    verdict=c.get("verdict", "agree"),
                )
            )
        elif isinstance(c, str):
            claims_list.append(
                ClaimItem(
                    id=f"C{i:03d}",
                    claim=c,
                    source_a=None,
                    source_b=None,
                    verdict="agree",
                )
            )

    return CompareResponse(
        summary=summary_str,
        similarities=similarities_list,
        differences=differences_list,
        claims=claims_list,
        doc_a_name=doc_a.filename,
        doc_b_name=doc_b.filename,
    )
