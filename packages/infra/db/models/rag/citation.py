
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin

class Citation(Base, UUIDPk, TimestampMixin):
    __tablename__ = "citations"
    __table_args__ = {"schema": "rag"}

    retrieval_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[Optional[float]]
