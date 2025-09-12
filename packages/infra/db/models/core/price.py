
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class Price(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "prices"
    __table_args__ = {"schema": "core"}

    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.product_variants.id", ondelete="CASCADE"))
    currency: Mapped[str] = mapped_column(String(3), default="VND", nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    compare_at: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    effective_at: Mapped[Optional[str]]  # TIMESTAMPTZ at DB

    variant: Mapped["ProductVariant"] = relationship(back_populates="prices")
