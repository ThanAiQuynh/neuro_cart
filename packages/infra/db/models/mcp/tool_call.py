
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base, UUIDPk, TimestampMixin

class ToolCall(Base, UUIDPk, TimestampMixin):
    __tablename__ = "tool_calls"
    __table_args__ = {"schema": "mcp"}

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat.agent_runs.id"),
        nullable=False
    )
    provider_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mcp.tool_providers.id"),
        nullable=True
    )
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    arguments: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String, default="success", nullable=False)
    latency_ms: Mapped[Optional[int]]

    provider: Mapped[Optional["ToolProvider"]] = relationship(back_populates="calls")
    run: Mapped["AgentRun"] = relationship()