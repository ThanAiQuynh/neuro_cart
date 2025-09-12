from __future__ import annotations
import os
from typing import Optional
from uuid import UUID
from datetime import timedelta

from dotenv import load_dotenv
from pydantic import BaseModel

from .dto import (
    UserDTO, AccessTokenDTO, RegisterInput, LoginInput, AssignRoleInput,
    UpdateProfileInput, ChangePasswordInput, AddressInput,
    user_to_dto, address_to_dto, AddressDTO
)
from ..errors import AlreadyExists, AuthenticationError
from ..ports.identity import IUserRepo, IRoleRepo, ICustomerRepo, IAddressRepo
from ..ports.security_async import IAsyncPasswordHasher, IAsyncTokenService

load_dotenv()
ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRES_HOURS", "12"))
DEFAULT_ACCESS_TOKEN_TTL = timedelta(ACCESS_TOKEN_EXPIRES_HOURS)
DEFAULT_CUSTOMER_ROLE = os.getenv('DEFAULT_CUSTOMER_ROLE', 'customer')


class RegisterUser:
    def __init__(
        self,
        users: IUserRepo,
        roles: IRoleRepo,
        customers: ICustomerRepo,
        hasher: IAsyncPasswordHasher,
    ) -> None:
        self.users = users
        self.roles = roles
        self.customers = customers
        self.hasher = hasher

    async def execute(self, data: RegisterInput) -> UserDTO:
        # Check duplicate email
        try:
            _ = await self.users.search_by_email(data.email)
            raise AlreadyExists("Email already in use")
        except Exception as e:
            if e.__class__.__name__ not in {"NotFoundError", "NotFound"}:
                pass

        hashed = await self.hasher.hash(data.password)

        # Thin object; infra repo should translate to ORM entity
        user = type("Obj", (), {})()
        user.email = str(data.email)
        user.password_hash = hashed
        user.full_name = data.full_name
        user.phone = data.phone
        user.is_active = True

        user = await self.users.add(user, commit=True, refresh=True)

        # Ensure role & assign
        await self.roles.ensure(DEFAULT_CUSTOMER_ROLE, name="Customer", commit=False)
        await self.users.add_role(user, DEFAULT_CUSTOMER_ROLE, commit=False)

        # Ensure customer row
        await self.customers.ensure_for_user(user.id, tier="standard", commit=True)

        return user_to_dto(user)

class LoginUser:
    def __init__(
        self,
        users: IUserRepo,
        hasher: IAsyncPasswordHasher,
        tokens: IAsyncTokenService,
        access_ttl: Optional[timedelta] = None,
    ) -> None:
        self.users = users
        self.hasher = hasher
        self.tokens = tokens
        self.access_ttl = access_ttl or DEFAULT_ACCESS_TOKEN_TTL

    async def execute(self, data: LoginInput) -> tuple[UserDTO, AccessTokenDTO]:
        try:
            user = await self.users.search_by_email(data.email)
        except Exception:
            raise AuthenticationError("Invalid credentials")

        if not getattr(user, "is_active", True):
            raise AuthenticationError("User is inactive")

        if not await self.hasher.verify(data.password, getattr(user, "password_hash")):
            raise AuthenticationError("Invalid credentials")

        token = await self.tokens.create_access_token(
            str(getattr(user, "id")),
            expires_delta=self.access_ttl,
            extra={"email": str(getattr(user, "email"))},
        )
        return user_to_dto(user), AccessTokenDTO(access_token=token)


class AssignRole:
    def __init__(self, users: IUserRepo, roles: IRoleRepo) -> None:
        self.users = users
        self.roles = roles

    async def execute(self, data: AssignRoleInput) -> None:
        await self.roles.ensure(data.role_code, name=data.role_code.title())
        user = await self.users.get(data.user_id)
        await self.users.add_role(user, data.role_code, commit=True)


class UpdateProfile:
    def __init__(self, users: IUserRepo) -> None:
        self.users = users

    async def execute(self, data: UpdateProfileInput) -> UserDTO:
        user = await self.users.get(data.user_id)
        patch = {}
        if data.full_name is not None:
            patch["full_name"] = data.full_name
        if data.phone is not None:
            patch["phone"] = data.phone
        user = await self.users.update(user, patch, commit=True, refresh=True)
        return user_to_dto(user)


class ChangePassword:
    def __init__(self, users: IUserRepo, hasher: IAsyncPasswordHasher) -> None:
        self.users = users
        self.hasher = hasher

    async def execute(self, data: ChangePasswordInput) -> None:
        user = await self.users.get(data.user_id)
        if not await self.hasher.verify(data.old_password, getattr(user, "password_hash")):
            raise AuthenticationError("Old password incorrect")
        new_hash = await self.hasher.hash(data.new_password)
        await self.users.update(user, {"password_hash": new_hash}, commit=True, refresh=False)


class AddAddress:
    def __init__(self, addresses: IAddressRepo) -> None:
        self.addresses = addresses

    async def execute(self, data: AddressInput) -> AddressDTO:
        addr = type("Obj", (), {})()
        for k, v in data.model_dump().items():
            setattr(addr, k, v)
        saved = await self.addresses.add(addr, commit=True, refresh=True)
        if data.is_default:
            await self.addresses.set_default(data.customer_id, getattr(saved, "id"), commit=True)
            setattr(saved, "is_default", True)
        return address_to_dto(saved)


class SetDefaultAddress:
    def __init__(self, addresses: IAddressRepo) -> None:
        self.addresses = addresses

    async def execute(self, customer_id: UUID, address_id: UUID) -> None:
        await self.addresses.set_default(customer_id, address_id, commit=True)
