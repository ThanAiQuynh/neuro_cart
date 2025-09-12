
from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, INET
from ..base import Base, UUIDPk, TimestampMixin

class RefreshToken(Base, UUIDPk):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        # unique (jti)
        UniqueConstraint("jti", name="uq_tokens_jti"),

        # unique partial (family_id) WHERE revoked_at IS NULL
        Index(
            "uq_tokens_family_active",
            "family_id",
            unique=True,
            postgresql_where=(lambda: RefreshToken.revoked_at.is_(None))  # tham chiếu field
        ),

        # index (user_id, expires_at)
        Index("ix_tokens_userid_expires", "user_id", "expires_at"),

        {"schema": "ops"},
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ops.auth_sessions.id"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id"),
        nullable=False
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        nullable=False
    )
    jti: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    replaced_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(nullable=True)

    session: Mapped["AuthSession"] = relationship(back_populates="refresh_tokens")
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")