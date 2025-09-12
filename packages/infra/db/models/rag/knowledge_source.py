
from __future__ import annotations
from typing import List, Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from ..base import Base, UUIDPk, TimestampMixin

class KnowledgeSource(Base, UUIDPk, TimestampMixin):
    __tablename__ = "knowledge_sources"
    __table_args__ = {"schema": "rag"}

    name: Mapped[str] = mapped_column(String, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # manual/datasheet/warranty/faq/blog/web
    url: Mapped[Optional[str]]
    metadata_: Mapped[dict] = mapped_column("metadata",JSONB, default=dict, nullable=False)

    documents: Mapped[List["Document"]] = relationship(back_populates="source", cascade="all, delete-orphan")
