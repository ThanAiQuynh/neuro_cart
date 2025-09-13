from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import TIMESTAMP, ForeignKey, Index, desc, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, INET
from ..base import Base, UUIDPk, TimestampMixin


class AuthSession(Base, UUIDPk, TimestampMixin):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        Index("ix_auth_sessions_userid_lastseen", "user_id", "last_seen_at"),
        Index("live_sessions_partial", "user_id",
            postgresql_where=text("revoked_at IS NULL")),
        {"schema": "ops"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id"),
        nullable=False
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="auth_sessions")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
