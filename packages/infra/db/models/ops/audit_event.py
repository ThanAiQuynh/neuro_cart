from sqlalchemy import BigInteger, ForeignKey, Text, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from ..base import Base, UUIDPk


class AuditLog(Base, UUIDPk):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_created_at", "created_at".desc()),
        Index("ix_audit_logs_meta_gin", "meta", postgresql_using="gin"),
        {"schema": "ops"},
    )

    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("core.users.id"), 
        nullable=True
    )
    event: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    user: Mapped["User"] = relationship(back_populates="audit_logs")
