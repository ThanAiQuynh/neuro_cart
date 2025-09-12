
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserDTO(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    roles: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None

class AccessTokenDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterInput(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class AssignRoleInput(BaseModel):
    user_id: UUID
    role_code: str

class UpdateProfileInput(BaseModel):
    user_id: Optional[UUID] = None  # to be set in the endpoint
    full_name: Optional[str] = None
    phone: Optional[str] = None

class ChangePasswordInput(BaseModel):
    user_id: Optional[UUID] = None
    old_password: str
    new_password: str

class AddressInput(BaseModel):
    customer_id: Optional[UUID] = None
    label: Optional[str] = None
    recipient: str
    phone: Optional[str] = None
    line1: str
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: str
    is_default: bool = False

class AddressDTO(BaseModel):
    id: Optional[UUID] = None
    label: Optional[str] = None
    recipient: str
    phone: Optional[str] = None
    line1: str
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: str
    is_default: bool = False

def user_to_dto(user: object) -> UserDTO:
    roles = []
    if hasattr(user, "roles") and getattr(user, "roles"):
        roles = [getattr(r, "code", None) or getattr(r, "name", None) for r in user.roles if r]
    return UserDTO(
        id=getattr(user, "id"),
        email=getattr(user, "email"),
        full_name=getattr(user, "full_name", None),
        phone=getattr(user, "phone", None),
        is_active=getattr(user, "is_active", True),
        roles=roles,
        created_at=getattr(user, "created_at", None),
    )

def address_to_dto(addr: object) -> AddressDTO:
    return AddressDTO(
        id=getattr(addr, "id"),
        label=getattr(addr, "label", None),
        recipient=getattr(addr, "recipient"),
        phone=getattr(addr, "phone", None),
        line1=getattr(addr, "line1"),
        line2=getattr(addr, "line2", None),
        city=getattr(addr, "city", None),
        state=getattr(addr, "state", None),
        postal_code=getattr(addr, "postal_code", None),
        country_code=getattr(addr, "country_code"),
        is_default=getattr(addr, "is_default", False),
    )
