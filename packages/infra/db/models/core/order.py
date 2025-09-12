
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin

class Order(Base, UUIDPk, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = {"schema": "core"}

    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("core.customers.id", ondelete="SET NULL"))
    billing_addr_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("core.addresses.id"))
    shipping_addr_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("core.addresses.id"))
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="VND", nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    discount_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    tax_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    shipping_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    grand_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    shipments: Mapped[List["Shipment"]] = relationship(back_populates="order", cascade="all, delete-orphan")
