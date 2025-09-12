
from __future__ import annotations
from typing import List
from sqlalchemy import String, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class Brand(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "brands"
    __table_args__ = (
        Index("ux_brands_slug_live", "slug", unique=True, postgresql_where=text("deleted_at IS NULL")),
        {"schema": "core"}
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False)

    products: Mapped[List["Product"]] = relationship(back_populates="brand")
