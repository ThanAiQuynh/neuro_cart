
from __future__ import annotations
from datetime import timedelta
from ..settings import settings
from packages.infra.security.passwords_async import AsyncBcryptHasher  # type: ignore
from packages.infra.security.tokens_async import AsyncJWTService  # type: ignore

_password_hasher = AsyncBcryptHasher(rounds=12)
_token_service = AsyncJWTService(
    secret=settings.JWT_SECRET,
    algorithm=settings.JWT_ALG,
    issuer=settings.JWT_ISS,
    audience=settings.JWT_AUD,
    default_ttl=timedelta(hours=12),
)

async def get_password_hasher() -> AsyncBcryptHasher:
    return _password_hasher

async def get_token_service() -> AsyncJWTService:
    return _token_service
