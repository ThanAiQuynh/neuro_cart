
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin

class Customer(Base, UUIDPk, TimestampMixin):
    __tablename__ = "customers"
    __table_args__ = {"schema": "core"}

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"), unique=True)
    tier: Mapped[str] = mapped_column(String, default="standard")

    user: Mapped[Optional["User"]] = relationship(back_populates="customer")
    addresses: Mapped[List["Address"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
