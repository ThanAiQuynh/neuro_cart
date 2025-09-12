
from __future__ import annotations
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from packages.infra.db.session import SessionLocal
from packages.infra.repos.core.address_repo import AddressRepo
from packages.infra.repos.core.customer_repo import CustomerRepo
from packages.infra.repos.core.role_repo import RoleRepo
from packages.infra.repos.core.user_repo import UserRepo
from packages.infra.security.passwords import default_password_hasher, BcryptPasswordHasher
from packages.infra.security.tokens import JWTService

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_repo(db: Session = Depends(get_db)) -> UserRepo:
    return UserRepo(db)

def get_role_repo(db: Session = Depends(get_db)) -> RoleRepo:
    return RoleRepo(db)

def get_customer_repo(db: Session = Depends(get_db)) -> CustomerRepo:
    return CustomerRepo(db)

def get_address_repo(db: Session = Depends(get_db)) -> AddressRepo:
    return AddressRepo(db)

def get_password_hasher() -> BcryptPasswordHasher:
    return default_password_hasher()

def get_token_service() -> JWTService:
    return JWTService()
