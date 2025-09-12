
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import Integer, UniqueConstraint, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base

class ReturnItem(Base):
    __tablename__ = "return_items"
    __table_args__ = (
        UniqueConstraint("return_id", "order_item_id", name="uq_return_items_return_item"),
        CheckConstraint("qty > 0", name="ck_return_items_qty_pos"),
        {"schema": "core"}
    )

    return_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.returns.id", ondelete="CASCADE"), primary_key=True)
    order_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.order_items.id", ondelete="CASCADE"), primary_key=True)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    condition: Mapped[Optional[str]]

    return_: Mapped["Return"] = relationship(back_populates="items")
