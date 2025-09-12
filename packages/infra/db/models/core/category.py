
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import String, Index, text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class Category(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "categories"
    __table_args__ = (
        Index("ux_categories_slug_live", "slug", unique=True, postgresql_where=text("deleted_at IS NULL")),
        {"schema": "core"}
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("core.categories.id", ondelete="SET NULL"))

    parent: Mapped[Optional["Category"]] = relationship(remote_side="Category.id")
    products: Mapped[List["Product"]] = relationship(
        secondary="core.product_categories",
        back_populates="categories",
        lazy="selectin"
    )

class ProductCategory(Base):
    __tablename__ = "product_categories"
    __table_args__ = (
        UniqueConstraint("product_id", "category_id", name="uq_product_categories_product_category"),
        {"schema": "core"}
    )
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.products.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.categories.id", ondelete="CASCADE"), primary_key=True)
