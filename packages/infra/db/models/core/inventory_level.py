
from __future__ import annotations
import uuid
from sqlalchemy import Integer, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, TimestampMixin, SoftDeleteMixin

class InventoryLevel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "inventory_levels"
    __table_args__ = (
        UniqueConstraint("variant_id", "location_id", name="uq_inventory_levels_variant_location"),
        {"schema": "core"}
    )

    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.product_variants.id", ondelete="CASCADE"), primary_key=True)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.inventory_locations.id", ondelete="CASCADE"), primary_key=True)
    on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    variant: Mapped["ProductVariant"] = relationship(back_populates="inventory_levels")
    location: Mapped["InventoryLocation"] = relationship(back_populates="levels")
