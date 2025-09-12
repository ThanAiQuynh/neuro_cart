
from __future__ import annotations
from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    users: Mapped[List["User"]] = relationship(
        secondary="core.user_roles",
        back_populates="roles",
        lazy="selectin"
    )
