
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base, UUIDPk

class Payment(Base, UUIDPk):
    __tablename__ = "payments"
    __table_args__ = {"schema": "core"}

    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.orders.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    txn_ref: Mapped[Optional[str]]
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB)

    order: Mapped["Order"] = relationship(back_populates="payments")
