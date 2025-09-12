
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin

class AgentRun(Base, UUIDPk, TimestampMixin):
    __tablename__ = "agent_runs"
    __table_args__ = {"schema": "chat"}

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat.chat_sessions.id"),  # <-- thêm FK
        nullable=False
    )
    objective: Mapped[Optional[str]]
    status: Mapped[str] = mapped_column(String, default="running", nullable=False)
    started_at: Mapped[Optional[str]]
    finished_at: Mapped[Optional[str]]

    session: Mapped["ChatSession"] = relationship(back_populates="runs")
