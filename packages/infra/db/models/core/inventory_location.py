
from __future__ import annotations
from typing import List, Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base, UUIDPk, TimestampMixin

class InventoryLocation(Base, UUIDPk, TimestampMixin):
    __tablename__ = "inventory_locations"
    __table_args__ = {"schema": "core"}

    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[Optional[str]]

    levels: Mapped[List["InventoryLevel"]] = relationship(back_populates="location")
