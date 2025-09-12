
from __future__ import annotations
"""
SQLAlchemy 2.0 Declarative Base & Mixins
- Stable naming convention for Alembic
- UUID PK helper
- Timestamp & SoftDelete mixins
- Vector type shim (pgvector if available, else ARRAY(double precision))
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

# Optional pgvector
try:
    from pgvector.sqlalchemy import Vector as PgVector  # type: ignore
except Exception:  # pragma: no cover
    PgVector = None  # type: ignore

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Float

def Vector(dim: int):
    if PgVector is not None:
        return PgVector(dim)   # pgvector vector(dim)
    # fallback: dùng ARRAY(double precision) thay vì vector
    return ARRAY(Float)         # hoặc ARRAY(Float(asdecimal=False))

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=NAMING_CONVENTION)

class Base(DeclarativeBase):
    metadata = metadata

class UUIDPk:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )

class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    delete_reason: Mapped[Optional[str]] = mapped_column(nullable=True)
