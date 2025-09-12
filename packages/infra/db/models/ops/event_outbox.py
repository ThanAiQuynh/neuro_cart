
from __future__ import annotations
import uuid
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base, UUIDPk, TimestampMixin

class EventOutbox(Base, UUIDPk, TimestampMixin):
    __tablename__ = "event_outbox"
    __table_args__ = {"schema": "ops"}

    aggregate: Mapped[str] = mapped_column(String, nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
