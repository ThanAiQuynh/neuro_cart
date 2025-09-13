import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, BYTEA, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, UUIDPk


class OAuthAccount(Base, UUIDPk):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
        {"schema": "core"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(Text, nullable=False)
    provider_user_id: Mapped[str] = mapped_column(Text, nullable=False)

    access_token_encrypted: Mapped[Optional[bytes]] = mapped_column(BYTEA, nullable=True)
    refresh_token_encrypted: Mapped[Optional[bytes]] = mapped_column(BYTEA, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    # relationship ngược với User
    user: Mapped["User"] = relationship(back_populates="oauth_accounts")
