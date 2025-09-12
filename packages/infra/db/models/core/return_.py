
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base, UUIDPk

class Return(Base, UUIDPk):
    __tablename__ = "returns"
    __table_args__ = {"schema": "core"}

    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("core.orders.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String, default="requested", nullable=False)
    reason: Mapped[Optional[str]]

    items: Mapped[List["ReturnItem"]] = relationship(back_populates="return_", cascade="all, delete-orphan")
