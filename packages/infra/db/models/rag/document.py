
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class Document(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "documents"
    __table_args__ = {"schema": "rag"}

    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag.knowledge_sources.id"),  # <-- thêm FK
        nullable=True
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("core.products.id"),  # <-- thêm FK
        nullable=True
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("core.product_variants.id"),  # <-- thêm FK
        nullable=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    lang: Mapped[str] = mapped_column(String, default="vi")
    tags: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    latest_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    source: Mapped[Optional["KnowledgeSource"]] = relationship(back_populates="documents")
    versions: Mapped[List["DocumentVersion"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[List["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    product: Mapped[Optional["Product"]] = relationship()
    variant: Mapped[Optional["ProductVariant"]] = relationship()
