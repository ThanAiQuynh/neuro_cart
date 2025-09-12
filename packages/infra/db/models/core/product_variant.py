
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import String, Index, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class ProductVariant(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "product_variants"
    __table_args__ = (
        Index("ux_variants_sku_live", "sku", unique=True, postgresql_where=text("deleted_at IS NULL")),
        {"schema": "core"}
    )

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.products.id", ondelete="CASCADE"))
    sku: Mapped[str] = mapped_column(String, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    barcode: Mapped[Optional[str]]
    weight_grams: Mapped[Optional[int]]
    dimensions_mm: Mapped[Optional[dict]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)

    product: Mapped["Product"] = relationship(back_populates="variants")
    inventory_levels: Mapped[List["InventoryLevel"]] = relationship(back_populates="variant", cascade="all, delete-orphan")
    prices: Mapped[List["Price"]] = relationship(back_populates="variant", cascade="all, delete-orphan")
