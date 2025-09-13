
from __future__ import annotations
from datetime import datetime, timedelta
import hashlib
from time import timezone
from typing import Annotated
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from apps.api.presenters.auth_cookies import AuthCookieManager
from packages.core.application.errors import AlreadyExists, AuthenticationError

from apps.api.di.security_async import get_password_hasher, get_token_service
from apps.api.di.auth_bearer import get_current_payload
from apps.api.di.container import get_auth_cookie_manager, get_auth_session_repo, get_login_attempt_repo, get_refresh_token_pepper, get_refresh_token_repo, get_refresh_token_ttl, get_user_repo, get_role_repo, get_customer_repo, get_address_repo, get_access_token_ttl
from packages.core.application.identity.dto import AddressDTO, AddressInput, ChangePasswordInput, LoginInput, RegisterInput, UpdateProfileInput, UserDTO, user_to_dto
from packages.core.application.identity.use_cases import AddAddress, ChangePassword, LoginUser, RegisterUser, UpdateProfile
from packages.core.application.ports.security_async import IAsyncPasswordHasher, IAsyncTokenService
from packages.infra.repos.core.address_repo import AddressRepo
from packages.infra.repos.core.auth_session_repo import AuthSessionRepo
from packages.infra.repos.core.customer_repo import CustomerRepo
from packages.infra.repos.core.login_attemp_repo import LoginAttemptRepo
from packages.infra.repos.core.refresh_token_repo import RefreshTokenRepo
from packages.infra.repos.core.role_repo import RoleRepo
from packages.infra.repos.core.user_repo import UserRepo

router = APIRouter(prefix="/auth", tags=["auth"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginResponse(BaseModel):
    user: UserDTO
    token: TokenResponse

@router.post("/register", response_model=UserDTO, status_code=201)
async def register_user(
    body: RegisterInput,
    users: Annotated[UserRepo, Depends(get_user_repo)],
    roles: Annotated[RoleRepo, Depends(get_role_repo)],
    customers: Annotated[CustomerRepo, Depends(get_customer_repo)],
    hasher: Annotated[IAsyncPasswordHasher, Depends(get_password_hasher)],
):
    uc = RegisterUser(users, roles, customers, hasher)
    try:
        return await uc.execute(body)
    except AlreadyExists as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: Request,
    body: LoginInput,
    users: Annotated[UserRepo, Depends(get_user_repo)],
    hasher: Annotated[IAsyncPasswordHasher, Depends(get_password_hasher)],
    tokens: Annotated[IAsyncTokenService, Depends(get_token_service)],
    access_ttl: Annotated[timedelta, Depends(get_access_token_ttl)],
    refresh_ttl: Annotated[timedelta, Depends(get_refresh_token_ttl)],
    cookies: Annotated[AuthCookieManager, Depends(get_auth_cookie_manager)],
    attempts: Annotated[LoginAttemptRepo, Depends(get_login_attempt_repo)],
    sessions: Annotated[AuthSessionRepo, Depends(get_auth_session_repo)],
    refresh_repo: Annotated[RefreshTokenRepo, Depends(get_refresh_token_repo)],
    refresh_pepper: Annotated[str, Depends(get_refresh_token_pepper)],
):
    now = datetime.now(timezone.utc)
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    # 1) Rate-limit/lockout
    locked_until = await attempts.is_locked(body.email, ip or "")
    if locked_until and locked_until > now:
        await attempts.add(email=body.email, ip=ip or "", success=False)
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")

    # 2) Tìm user + verify mật khẩu
    try:
        user = await users.by_email(body.email)
    except Exception:
        await attempts.add(email=body.email, ip=ip or "", success=False)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not getattr(user, "is_active", True):
        await attempts.add(email=body.email, ip=ip or "", success=False)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not await hasher.verify(body.password, getattr(user, "password_hash")):
        await attempts.add(email=body.email, ip=ip or "", success=False)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await attempts.add(email=body.email, ip=ip or "", success=True)

    # 3) (MFA: later) — nếu bật thì return requires_mfa tại đây

    # 4) Tạo auth_session
    session = await sessions.create(user_id=getattr(user, "id"), ip=ip, user_agent=ua)

    # 5) Issue refresh (jti, family_id) + lưu HASH vào ops.refresh_tokens
    jti = uuid.uuid4()
    family_id = uuid.uuid4()
    refresh_payload = {"type": "refresh", "jti": str(jti), "fam": str(family_id), "sid": str(getattr(session, "id"))}
    refresh_token = await tokens.create_refresh_token(
        str(getattr(user, "id")),
        expires_delta=refresh_ttl,
        extra=refresh_payload,
    )
    token_hash = hashlib.sha256((refresh_token + refresh_pepper).encode("utf-8")).hexdigest()
    await refresh_repo.add(
        user_id=getattr(user, "id"),
        session_id=getattr(session, "id"),
        jti=jti,
        family_id=family_id,
        token_hash=token_hash,
        expires_at=now + refresh_ttl,
    )

    # 6) Issue access JWT
    roles = [r.code for r in getattr(user, "roles", [])]
    access_payload = {"type": "access", "sid": str(getattr(session, "id")), "roles": roles, "email": str(getattr(user, "email"))}
    access_token = await tokens.create_access_token(
        str(getattr(user, "id")),
        expires_delta=access_ttl,
        extra=access_payload,
    )

    # 7) Update users.last_login_at
    await users.update(user, {"last_login_at": now}, commit=True, refresh=False)

    # 8) Set cookie access_token & refresh_token
    user_dto = user_to_dto(user)
    resp = JSONResponse(
        content=LoginResponse(
            user=user_dto,
            token=TokenResponse(access_token=access_token, token_type="bearer"),
        ).model_dump(mode="json")
    )
    cookies.set_access(resp, access_token, access_ttl)          # đã có sẵn phía bạn
    cookies.set_refresh(resp, refresh_token, refresh_ttl)       # cần thêm method này
    return resp

@router.post("/logout", status_code=204)
async def logout():
    resp = JSONResponse(content=None, status_code=204)
    resp.delete_cookie("access_token")   # xoá cookie
    return resp

@router.get("/me", response_model=UserDTO)
async def me(
    payload: Annotated[dict, Depends(get_current_payload)],
    users: Annotated[UserRepo, Depends(get_user_repo)],
):
    user = await users.get(UUID(payload["sub"]))
    return UserDTO.model_validate(user.__dict__ | {"roles": [r.code for r in getattr(user, "roles", [])]})

# Profile
profile_router = APIRouter(prefix="/users", tags=["users"])

@profile_router.patch("/{user_id}/profile", response_model=UserDTO)
async def update_profile(
    user_id: UUID,
    body: UpdateProfileInput,
    users: Annotated[UserRepo, Depends(get_user_repo)],
    payload: Annotated[dict, Depends(get_current_payload)],
):
    if str(payload["sub"]) != str(user_id) and "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Forbidden")
    uc = UpdateProfile(users)
    body.user_id = user_id
    return await uc.execute(body)

@profile_router.post("/{user_id}/change-password", status_code=204)
async def change_password(
    user_id: UUID,
    body: ChangePasswordInput,
    users: Annotated[UserRepo, Depends(get_user_repo)],
    hasher: Annotated[IAsyncPasswordHasher, Depends(get_password_hasher)],
    payload: Annotated[dict, Depends(get_current_payload)],
):
    if str(payload["sub"]) != str(user_id) and "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Forbidden")
    uc = ChangePassword(users, hasher)
    await uc.execute(body.model_copy(update={"user_id": user_id}))
    return

# Addresses (current user)
addresses_router = APIRouter(prefix="/me/addresses", tags=["addresses"])

@addresses_router.get("", response_model=list[AddressDTO])
async def list_my_addresses(
    customers: Annotated[CustomerRepo, Depends(get_customer_repo)],
    addresses: Annotated[AddressRepo, Depends(get_address_repo)],
    payload: Annotated[dict, Depends(get_current_payload)],
):
    c = await customers.by_user_id(UUID(payload["sub"]))
    rows = await addresses.list_by_customer(c.id)
    return [AddressDTO.model_validate(r.__dict__) for r in rows]

@addresses_router.post("", response_model=AddressDTO, status_code=201)
async def add_my_address(
    body: AddressInput,
    customers: Annotated[CustomerRepo, Depends(get_customer_repo)],
    addresses: Annotated[AddressRepo, Depends(get_address_repo)],
    payload: Annotated[dict, Depends(get_current_payload)],
):
    c = await customers.by_user_id(UUID(payload["sub"]))
    body.customer_id = c.id
    uc = AddAddress(addresses)
    return await uc.execute(body)
