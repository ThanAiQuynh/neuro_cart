
from __future__ import annotations
from datetime import timedelta
from fastapi import Depends
from sqlalchemy.orm import Session

from apps.api.presenters.auth_cookies import AuthCookieManager, CookieConfig
from packages.infra.db.session import get_session
from packages.infra.repos.core.address_repo import AddressRepo
from packages.infra.repos.core.customer_repo import CustomerRepo
from packages.infra.repos.core.role_repo import RoleRepo
from packages.infra.repos.core.user_repo import UserRepo
from packages.infra.security.passwords import default_password_hasher, BcryptPasswordHasher
from packages.infra.security.tokens import TokenService
from apps.api.settings import settings

# ---------- Security providers ----------
def get_password_hasher() -> BcryptPasswordHasher:
    return default_password_hasher()

def get_token_service() -> TokenService:
    return TokenService(settings.secret_key)

def get_auth_cookie_manager() -> AuthCookieManager:
    cfg = CookieConfig(
        access_name=settings.cookie_access_name,
        refresh_name=settings.cookie_refresh_name,
        domain=settings.cookie_domain,
        path=settings.cookie_path,
        secure=settings.cookie_secure,
        httponly=settings.cookie_httponly,
        samesite=settings.cookie_samesite,
    )
    return AuthCookieManager(cfg)

# ---------- Repos ----------
def get_user_repo(db: Session = Depends(get_session)) -> UserRepo:
    return UserRepo(db)

def get_role_repo(db: Session = Depends(get_session)) -> RoleRepo:
    return RoleRepo(db)

def get_customer_repo(db: Session = Depends(get_session)) -> CustomerRepo:
    return CustomerRepo(db)

def get_address_repo(db: Session = Depends(get_session)) -> AddressRepo:
    return AddressRepo(db)

# ---------- App config ----------
def get_access_token_ttl() -> timedelta:
    return timedelta(hours=settings.access_token_expires_hours)
