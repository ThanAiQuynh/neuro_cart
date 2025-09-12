
from __future__ import annotations
import uuid
from sqlalchemy import Integer, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base

class ShipmentItem(Base):
    __tablename__ = "shipment_items"
    __table_args__ = (
        UniqueConstraint("shipment_id", "order_item_id", name="uq_shipment_items_shipment_item"),
        {"schema": "core"}
    )

    shipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.shipments.id", ondelete="CASCADE"), primary_key=True)
    order_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.order_items.id", ondelete="CASCADE"), primary_key=True)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)

    shipment: Mapped["Shipment"] = relationship(back_populates="items")
