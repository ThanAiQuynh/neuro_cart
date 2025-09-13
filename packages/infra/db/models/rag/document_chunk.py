
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, Text, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin, Vector

class DocumentChunk(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index(
            "ix_rag_document_chunks_embedding_live",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": "100"},
            postgresql_where=text("deleted_at IS NULL"),
        ),
        {"schema": "rag"}
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag.documents.id"),  # <-- thêm FK
        nullable=False
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag.document_versions.id"),  # <-- thêm FK
        nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[Optional[int]]
    embedding: Mapped[Optional[object]] = mapped_column(Vector(1536))
    metadata_: Mapped[dict] = mapped_column("metadata",JSONB, default=dict, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="chunks")
    version: Mapped["DocumentVersion"] = relationship(back_populates="chunks")
