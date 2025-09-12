
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class ChatMessage(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chat_messages"
    __table_args__ = {"schema": "chat"}

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat.chat_sessions.id"),  # <-- thêm FK
        nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    tokens_in: Mapped[Optional[int]]
    tokens_out: Mapped[Optional[int]]

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
    citations: Mapped[List["MessageCitation"]] = relationship(back_populates="message", cascade="all, delete-orphan")
