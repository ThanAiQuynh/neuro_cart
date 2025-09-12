
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import Boolean, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin

class Address(Base, UUIDPk, TimestampMixin):
    __tablename__ = "addresses"
    __table_args__ = {"schema": "core"}

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.customers.id", ondelete="CASCADE"))
    label: Mapped[Optional[str]]
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[Optional[str]]
    line1: Mapped[str] = mapped_column(String, nullable=False)
    line2: Mapped[Optional[str]]
    city: Mapped[Optional[str]]
    state: Mapped[Optional[str]]
    postal_code: Mapped[Optional[str]]
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer: Mapped["Customer"] = relationship(back_populates="addresses")
