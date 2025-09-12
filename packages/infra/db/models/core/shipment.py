
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk

class Shipment(Base, UUIDPk):
    __tablename__ = "shipments"
    __table_args__ = {"schema": "core"}

    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.orders.id", ondelete="CASCADE"))
    carrier: Mapped[Optional[str]]
    tracking_no: Mapped[Optional[str]]
    status: Mapped[str] = mapped_column(String, default="ready", nullable=False)
    shipped_at: Mapped[Optional[str]]
    delivered_at: Mapped[Optional[str]]

    order: Mapped["Order"] = relationship(back_populates="shipments")
    items: Mapped[List["ShipmentItem"]] = relationship(back_populates="shipment", cascade="all, delete-orphan")
