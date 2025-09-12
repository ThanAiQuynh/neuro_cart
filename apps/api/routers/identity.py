
from __future__ import annotations
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from apps.api.presenters.auth_cookies import AuthCookieManager
from packages.core.application.errors import AlreadyExists, AuthenticationError

from apps.api.di.security_async import get_password_hasher, get_token_service
from apps.api.di.auth_bearer import get_current_payload
from apps.api.di.container import get_auth_cookie_manager, get_user_repo, get_role_repo, get_customer_repo, get_address_repo, get_access_token_ttl
from packages.core.application.identity.dto import AddressDTO, AddressInput, ChangePasswordInput, LoginInput, RegisterInput, UpdateProfileInput, UserDTO
from packages.core.application.identity.use_cases import AddAddress, ChangePassword, LoginUser, RegisterUser, UpdateProfile
from packages.core.application.ports.security_async import IAsyncPasswordHasher, IAsyncTokenService
from packages.infra.repos.core.address_repo import AddressRepo
from packages.infra.repos.core.customer_repo import CustomerRepo
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
    body: LoginInput,
    users: Annotated[UserRepo, Depends(get_user_repo)],
    hasher: Annotated[IAsyncPasswordHasher, Depends(get_password_hasher)],
    tokens: Annotated[IAsyncTokenService, Depends(get_token_service)],
    access_ttl: Annotated[object, Depends(get_access_token_ttl)],  # timedelta
    cookies: Annotated[AuthCookieManager, Depends(get_auth_cookie_manager)],
):
    uc = LoginUser(users, hasher, tokens, access_ttl)
    try:
        user, token = await uc.execute(body)  # token có .access_token (pydantic)
        resp = JSONResponse(
            content=LoginResponse(
                user=user,
                token=TokenResponse(**token.model_dump())
            ).model_dump(mode="json")
        )
        # Set cookie access (TTL lấy từ DI; nếu token có TTL riêng thì dùng token.ttl)
        cookies.set_access(resp, token.access_token, access_ttl)
        return resp
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))

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
