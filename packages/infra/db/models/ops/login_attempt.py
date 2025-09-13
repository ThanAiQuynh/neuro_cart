from datetime import datetime
from sqlalchemy import Index, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import CITEXT, INET, TIMESTAMP
from ..base import Base, UUIDPk


class LoginAttempt(Base, UUIDPk):
    __tablename__ = "login_attempts"
    __table_args__ = (
        Index("ix_login_attempts_email_time", "email_canon", "attempted_at"),
        Index("ix_login_attempts_ip_time", "ip", "attempted_at"),
        {"schema": "ops"},
    )

    email_canon: Mapped[str] = mapped_column(CITEXT, nullable=False)
    ip: Mapped[str] = mapped_column(INET, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
