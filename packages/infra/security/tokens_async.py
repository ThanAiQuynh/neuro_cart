
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import jwt

from apps.api import settings
load_dotenv()
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
    
    async def create_refresh_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a refresh token for a given user.
        
        :param user_id: The user ID for whom the token is created.
        :param expires_delta: Optional expiration delta. Default 30 days.
        :param extra: Extra payload to add into the token.
        :return: Encoded JWT refresh token string.
        """
        if expires_delta is None:
            expires_delta = timedelta(os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", 30))

        expire = datetime.now(timezone.utc) + expires_delta

        payload = {
            "sub": str(user_id),        # subject = user id
            "exp": expire,              # expiry time
            "iat": datetime.now(timezone.utc),  # issued at
            "type": "refresh"           # distinguish refresh token
        }

        if extra:
            payload.update(extra)

        encoded_jwt = await asyncio.to_thread(jwt.encode, payload, self.secret, algorithm=self.algorithm)
        return encoded_jwt

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
