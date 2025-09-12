
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class Cart(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "carts"
    __table_args__ = {"schema": "core"}

    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("core.customers.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)

    items: Mapped[List["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")
