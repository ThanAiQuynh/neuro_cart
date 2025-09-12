
from __future__ import annotations
from packages.infra.security.passwords import default_password_hasher, BcryptPasswordHasher

def get_password_hasher() -> BcryptPasswordHasher:
    return default_password_hasher()
