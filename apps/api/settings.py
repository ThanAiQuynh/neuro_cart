
from __future__ import annotations
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    app_name: str = "AskGear API"
    debug: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    
    database_url_sync: str = Field(..., alias="DATABASE_URL_SYNC")
    database_url_async: str = Field(..., alias="DATABASE_URL_ASYNC")

    access_token_expires_hours: int = Field(default=12, env="ACCESS_TOKEN_EXPIRES_HOURS")
    default_customer_role: str = Field(default="customer", env="DEFAULT_CUSTOMER_ROLE")

    refresh_token_expires_days: int = Field(default=30, env="REFRESH_TOKEN_EXPIRES_DAYS")
    refresh_token_pepper: str = Field(env="REFRESH_TOKEN_PEPPER")

    # Legacy secret (if used elsewhere)
    secret_key: str = Field("dev-secret-key-change-me", env="SECRET_KEY")

    # JWT
    JWT_SECRET: str = Field(default="change-me-in-prod", env="JWT_SECRET")
    JWT_ALG: str = Field(default="HS256", env="JWT_ALG")
    JWT_ISS: str = Field(default="askgear", env="JWT_ISS")
    JWT_AUD: str | None = Field(default=None, env="JWT_AUD")

    # Cookie
    cookie_access_name: str = "access_token"
    cookie_refresh_name: str = "refresh_token"
    cookie_domain: str | None = None        # ví dụ ".example.com" ở prod
    cookie_path: str = "/"
    cookie_secure: bool = False             # True ở prod (HTTPS)
    cookie_httponly: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
