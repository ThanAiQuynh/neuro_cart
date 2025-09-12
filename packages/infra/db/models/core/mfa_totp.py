import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, BYTEA, TIMESTAMP, ARRAY, TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin


class MfaTotp(Base, TimestampMixin):
    __tablename__ = "mfa_totp"
    __table_args__ = {"schema": "core"}

    # user_id vừa là PK vừa là FK
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    secret_encrypted: Mapped[bytes] = mapped_column(BYTEA, nullable=False)

    # mảng các hash recovery codes
    recovery_codes_hash: Mapped[list[str]] = mapped_column(
        ARRAY(TEXT),
        nullable=False,
    )

    disabled_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Quan hệ ngược với User (nếu cần)
    user: Mapped["User"] = relationship(back_populates="mfa_totp", uselist=False)
