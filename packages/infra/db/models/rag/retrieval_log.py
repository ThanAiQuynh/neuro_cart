
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin, Vector

class RetrievalLog(Base, UUIDPk, TimestampMixin):
    __tablename__ = "retrieval_logs"
    __table_args__ = {"schema": "rag"}

    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat.chat_sessions.id"),
        nullable=True
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_embedding: Mapped[Optional[object]] = mapped_column(Vector(1536))
    top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    latency_ms: Mapped[Optional[int]]

    session: Mapped[Optional["ChatSession"]] = relationship()
