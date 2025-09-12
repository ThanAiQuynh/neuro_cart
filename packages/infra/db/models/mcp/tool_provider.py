
from __future__ import annotations
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from ..base import Base, UUIDPk, TimestampMixin

class ToolProvider(Base, UUIDPk, TimestampMixin):
    __tablename__ = "tool_providers"
    __table_args__ = {"schema": "mcp"}

    name: Mapped[str] = mapped_column(String, nullable=False)
    endpoint: Mapped[Optional[str]] = mapped_column(String)
    metadata_: Mapped[dict] = mapped_column("metadata",JSONB, default=dict, nullable=False)

    calls: Mapped[list["ToolCall"]] = relationship(back_populates="provider")
