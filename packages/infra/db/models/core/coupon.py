
from __future__ import annotations
from typing import Optional
from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from ..base import Base, UUIDPk, TimestampMixin

class Coupon(Base, UUIDPk, TimestampMixin):
    __tablename__ = "coupons"
    __table_args__ = {"schema": "core"}

    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # percent/fixed
    value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    max_uses: Mapped[Optional[int]]
    used_count: Mapped[int] = mapped_column(default=0, nullable=False)
    starts_at: Mapped[Optional[str]]
    ends_at: Mapped[Optional[str]]
    conditions: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
