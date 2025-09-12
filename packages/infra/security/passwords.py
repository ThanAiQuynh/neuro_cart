
from __future__ import annotations
import asyncio
import functools
from typing import Optional

# Prefer bcrypt (widely available); optionally support argon2 if installed.
try:
    import bcrypt
except Exception as e:  # pragma: no cover
    bcrypt = None  # type: ignore

try:
    from argon2 import PasswordHasher as Argon2Hasher
    from argon2.exceptions import VerifyMismatchError
except Exception:  # pragma: no cover
    Argon2Hasher = None  # type: ignore
    VerifyMismatchError = Exception  # type: ignore


async def _to_thread(func, *args, **kwargs):
    """Run a sync function in a thread, return its result."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


class BcryptPasswordHasher:
    """Async adapter over `bcrypt` with thread offloading."""
    def __init__(self, rounds: int = 12):
        if bcrypt is None:
            raise RuntimeError("bcrypt not installed. `pip install bcrypt`")
        self.rounds = rounds

    async def hash(self, plain: str) -> str:
        salt = await _to_thread(bcrypt.gensalt, self.rounds)
        digest: bytes = await _to_thread(bcrypt.hashpw, plain.encode("utf-8"), salt)
        return digest.decode("utf-8")

    async def verify(self, plain: str, hashed: str) -> bool:
        try:
            ok: bool = await _to_thread(bcrypt.checkpw, plain.encode("utf-8"), hashed.encode("utf-8"))
            return bool(ok)
        except Exception:
            return False


class Argon2PasswordHasher:
    """Async adapter over `argon2-cffi` with thread offloading."""
    def __init__(
        self,
        time_cost: int = 2,
        memory_cost: int = 102400,  # KiB
        parallelism: int = 8,
        hash_len: int = 32,
        salt_len: int = 16,
    ):
        if Argon2Hasher is None:
            raise RuntimeError("argon2-cffi not installed. `pip install argon2-cffi`")
        self._ph = Argon2Hasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=hash_len,
            salt_len=salt_len,
        )

    async def hash(self, plain: str) -> str:
        return await _to_thread(self._ph.hash, plain)

    async def verify(self, plain: str, hashed: str) -> bool:
        def _verify() -> bool:
            try:
                return bool(self._ph.verify(hashed, plain))
            except VerifyMismatchError:
                return False
            except Exception:
                return False
        return await _to_thread(_verify)


def default_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher(rounds=12)
