
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import CITEXT
from ..base import Base, UUIDPk, TimestampMixin

class User(Base, UUIDPk, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = {"schema": "core"}

    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[Optional[str]]
    phone: Mapped[Optional[str]]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    email_verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    failed_login_count: Mapped[int] = mapped_column(default=0, nullable=False)
    lock_until: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer: Mapped[Optional["Customer"]] = relationship(back_populates="user")
    roles: Mapped[List["Role"]] = relationship(
        secondary="core.user_roles",
        back_populates="users",
        lazy="selectin"
    )
    password_resets: Mapped[List["PasswordReset"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    auth_sessions: Mapped[List["AuthSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    mfa_totps: Mapped[List["MfaTotp"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["ApiKey"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
