import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Index, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin, UUIDPk


class PasswordReset(Base, UUIDPk, TimestampMixin):
    __tablename__ = "password_resets"
    __table_args__ = (
        Index(
            "uq_password_resets_user_active",
            "user_id",
            unique=True,
            postgresql_where=text("used_at IS NULL"),
        ),
        {"schema": "core"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("core.users.id"), 
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="password_resets")
