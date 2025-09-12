
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt

class AsyncJWTService:
    """Async JWT encode/decode (PyJWT) offloaded to threads."""
    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        default_ttl: timedelta = timedelta(hours=12),
    ) -> None:
        self.secret = secret
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.default_ttl = default_ttl

    async def create_access_token(
        self, subject: str, *, expires_delta: Optional[timedelta] = None, extra: Optional[Dict[str, Any]] = None
    ) -> str:
        now = datetime.now(timezone.utc)
        exp = now + (expires_delta or self.default_ttl)
        payload: Dict[str, Any] = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
        if self.issuer:
            payload["iss"] = self.issuer
        if self.audience:
            payload["aud"] = self.audience
        if extra:
            payload.update(extra)
        token = await asyncio.to_thread(jwt.encode, payload, self.secret, algorithm=self.algorithm)
        return token

    async def decode(self, token: str) -> dict:
        options = {"verify_aud": bool(self.audience)}
        payload = await asyncio.to_thread(
            jwt.decode,
            token,
            self.secret,
            algorithms=[self.algorithm],
            options=options,
            audience=self.audience,
            issuer=self.issuer,
        )
        return payload
