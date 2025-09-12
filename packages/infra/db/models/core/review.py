
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import SmallInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin

class Review(Base, UUIDPk, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = {"schema": "core"}

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.products.id", ondelete="CASCADE"))
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("core.product_variants.id", ondelete="SET NULL"))
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("core.customers.id", ondelete="SET NULL"))
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[Optional[str]]
    body: Mapped[Optional[str]]
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
