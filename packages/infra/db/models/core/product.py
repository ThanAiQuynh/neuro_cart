
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import Boolean, String, Text, Index, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class Product(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"
    __table_args__ = (
        Index("ux_products_slug_live", "slug", unique=True,
            postgresql_where=text("deleted_at IS NULL")),
        {"schema": "core"},
    )

    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("core.brands.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False)
    model_number: Mapped[Optional[str]]
    specs: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    description: Mapped[Optional[str]]
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    brand: Mapped[Optional["Brand"]] = relationship(back_populates="products")
    variants: Mapped[List["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    categories: Mapped[List["Category"]] = relationship(
        secondary="core.product_categories",
        back_populates="products",
        lazy="selectin"
    )
