
from __future__ import annotations
import uuid
from typing import List
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class DocumentVersion(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "document_versions"
    __table_args__ = {"schema": "rag"}

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag.documents.id"),  # <-- thêm FK
        nullable=False
    )
    version: Mapped[str] = mapped_column(String, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata",JSONB, default=dict, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="versions")
    chunks: Mapped[List["DocumentChunk"]] = relationship(back_populates="version")
