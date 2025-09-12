from __future__ import annotations
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL_ASYNC")  # ví dụ: postgresql+asyncpg://user:pass@localhost/dbname

# ✅ Dùng async engine
engine = create_async_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

# ✅ sessionmaker với AsyncSession
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    future=True,
)

# ✅ context manager async
@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# ✅ FastAPI dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
