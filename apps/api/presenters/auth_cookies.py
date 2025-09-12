from fastapi import Response
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class CookieConfig:
    access_name: str
    refresh_name: str
    domain: str | None
    path: str
    secure: bool
    httponly: bool
    samesite: str

class AuthCookieManager:
    def __init__(self, cfg: CookieConfig):
        self.cfg = cfg

    def set_access(self, resp: Response, token: str, ttl: timedelta) -> None:
        resp.set_cookie(
            key=self.cfg.access_name, value=token,
            max_age=int(ttl.total_seconds()),
            domain=self.cfg.domain, path=self.cfg.path,
            secure=self.cfg.secure, httponly=self.cfg.httponly,
            samesite=self.cfg.samesite,
        )

    def set_refresh(self, resp: Response, token: str, ttl: timedelta) -> None:
        resp.set_cookie(
            key=self.cfg.refresh_name, value=token,
            max_age=int(ttl.total_seconds()),
            domain=self.cfg.domain, path=self.cfg.path,
            secure=self.cfg.secure, httponly=self.cfg.httponly,
            samesite=self.cfg.samesite,
        )

    def clear(self, resp: Response) -> None:
        resp.delete_cookie(self.cfg.access_name, domain=self.cfg.domain, path=self.cfg.path)
        resp.delete_cookie(self.cfg.refresh_name, domain=self.cfg.domain, path=self.cfg.path)
