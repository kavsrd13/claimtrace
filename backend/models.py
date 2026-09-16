"""
SQLAlchemy ORM models for ClaimTrace.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class Session(Base):
    """A user session containing uploaded documents."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        exp = _as_utc(self.expires_at)
        return exp is not None and (datetime.now(UTC) > exp or self.deleted_at is not None)


class Document(Base):
    """An uploaded document belonging to a session."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    # Slot index: 0 = document A, 1 = document B
    slot: Mapped[int] = mapped_column(Integer, default=0)

    # Serialised JSON of chunk embeddings stored as pipe-separated base64
    # (kept simple to avoid a vector DB dependency)
    embeddings_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped[Session] = relationship("Session", back_populates="documents")
