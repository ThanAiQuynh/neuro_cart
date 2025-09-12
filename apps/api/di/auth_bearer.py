from __future__ import annotations
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .security_async import get_token_service
from packages.infra.security.tokens_async import AsyncJWTService  # type: ignore

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_payload(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    token_service: AsyncJWTService = Depends(get_token_service),
) -> dict:
    token: str | None = None

    # 1. Ưu tiên đọc cookie
    token = request.cookies.get("access_token")

    # 2. Nếu không có cookie, fallback sang Authorization header
    if not token and creds and creds.scheme.lower() == "bearer":
        token = creds.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = await token_service.decode(token)
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
