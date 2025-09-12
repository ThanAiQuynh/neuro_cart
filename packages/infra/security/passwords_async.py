
from __future__ import annotations
import asyncio
import bcrypt

class AsyncBcryptHasher:
    """Async bcrypt using asyncio.to_thread to avoid blocking the event loop."""
    def __init__(self, rounds: int = 12) -> None:
        self.rounds = rounds

    async def hash(self, plain: str) -> str:
        salt = await asyncio.to_thread(bcrypt.gensalt, self.rounds)
        hashed = await asyncio.to_thread(bcrypt.hashpw, plain.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    async def verify(self, plain: str, hashed: str) -> bool:
        try:
            ok = await asyncio.to_thread(bcrypt.checkpw, plain.encode("utf-8"), hashed.encode("utf-8"))
            return bool(ok)
        except Exception:
            return False
