# packages/infra/repos/ops_repos.py
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from packages.infra.db.models.ops.login_attempt import LoginAttempt

class LoginAttemptRepo:
    """Ghi log login và kiểm tra lockout theo cửa sổ thời gian."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        max_attempts: int = 5,
        window: timedelta = timedelta(minutes=15),
        lockout: timedelta = timedelta(minutes=15),
    ) -> None:
        # Khởi tạo repository với session và các tham số cấu hình:
        # max_attempts: số lần thử tối đa cho phép trong cửa sổ thời gian
        # window: khoảng thời gian để tính số lần thử
        # lockout: thời gian khóa tài khoản nếu vượt quá số lần thử
        self.s = session
        self.max_attempts = max_attempts
        self.window = window
        self.lockout = lockout

    async def is_locked(self, email: str, ip: str) -> Optional[datetime]:
        """
        Kiểm tra xem tài khoản có bị khóa do đăng nhập sai nhiều lần không.
        - email: email đăng nhập.
        - ip: địa chỉ IP của người dùng.
        Trả về thời điểm hết hạn khóa nếu bị khóa, ngược lại trả về None.
        """
        now = datetime.now(timezone.utc)
        since = now - self.window

        # Đếm số lần đăng nhập thất bại trong cửa sổ thời gian
        stmt = (
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.email == email,
                LoginAttempt.ip == ip,
                LoginAttempt.success.is_(False),
                LoginAttempt.created_at >= since,
            )
        )
        res = await self.s.execute(stmt)
        fail_count: int = int(res.scalar() or 0)

        if fail_count >= self.max_attempts:
            # Nếu vượt quá số lần cho phép, trả về thời điểm hết hạn khóa
            return now + self.lockout

        return None  # Không bị khóa

    async def add(self, *, email: str, ip: str, success: bool, commit: bool = True) -> None:
        """
        Ghi lại một lần đăng nhập (thành công hoặc thất bại).
        - email: email đăng nhập.
        - ip: địa chỉ IP của người dùng.
        - success: True nếu đăng nhập thành công, False nếu thất bại.
        - commit: Nếu True thì commit thay đổi vào DB ngay.
        """
        attempt = LoginAttempt(email=email, ip=ip, success=success)
        self.s.add(attempt)  # Thêm bản ghi vào session
        await self.s.flush()  # Đẩy thay đổi lên DB (chưa commit)
        if commit:
            await self.s.commit()  # Commit nếu được yêu cầu