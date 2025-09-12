
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class ChatSession(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chat_sessions"
    __table_args__ = {"schema": "chat"}

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id"),
        nullable=True
    )
    channel: Mapped[str] = mapped_column(String, default="web", nullable=False)
    persona: Mapped[Optional[str]] = mapped_column(String, default="customer_assistant")
    last_active_at: Mapped[Optional[str]]

    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    runs: Mapped[List["AgentRun"]] = relationship(back_populates="session", cascade="all, delete-orphan")
