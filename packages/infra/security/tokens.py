
from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

try:
    from jose import jwt  # type: ignore
except Exception as e:
    jwt = None  # type: ignore

class TokenService:
    def __init__(self, secret_key: str, algorithm: str = "HS256", issuer: str = "askgear", audience: Optional[str] = None):
        if jwt is None:
            raise RuntimeError("python-jose not installed. `pip install python-jose[cryptography]`")
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience

    def create_access_token(self, subject: str, *, expires_delta: Optional[timedelta] = None, extra: Optional[Dict[str, Any]] = None) -> str:
        now = datetime.now(timezone.utc)
        exp = now + (expires_delta or timedelta(hours=12))
        payload = {"sub": subject, "iat": int(now.timestamp()), "nbf": int(now.timestamp()), "exp": int(exp.timestamp()), "iss": self.issuer}
        if self.audience:
            payload["aud"] = self.audience
        if extra:
            payload.update(extra)
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode(self, token: str) -> dict:
        options = {"verify_aud": self.audience is not None}
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm], audience=self.audience, options=options)
