
from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..base import Base, UUIDPk, TimestampMixin, SoftDeleteMixin

class MediaAsset(Base, UUIDPk, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "media_assets"
    __table_args__ = {"schema": "core"}

    owner_type: Mapped[str] = mapped_column(String, nullable=False)  # product|variant
    owner_id: Mapped[uuid.UUID]
    url: Mapped[str] = mapped_column(Text, nullable=False)
    alt: Mapped[Optional[str]]
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
