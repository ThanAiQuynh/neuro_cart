from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy import bindparam

from packages.infra.db.models.ops.auth_session import AuthSession
from sqlalchemy.ext.asyncio import AsyncSession

class AuthSessionRepo:
    """Tạo phiên đăng nhập (ops.auth_sessions)."""

    def __init__(self, session: AsyncSession) -> None:
        # Khởi tạo repository với một phiên làm việc async của SQLAlchemy
        self.s = session

    async def create(self, *, user_id: UUID, ip: Optional[str], user_agent: Optional[str]) -> AuthSession:
        """
        Tạo một phiên đăng nhập mới cho người dùng.
        - user_id: ID của người dùng.
        - ip: Địa chỉ IP của người dùng (có thể None).
        - user_agent: Thông tin trình duyệt/thiết bị (có thể None).
        Trả về đối tượng AuthSession vừa tạo (đã có id).
        """
        sess = AuthSession(
            user_id=user_id,
            ip=bindparam("ip", ip, type_=INET()),
            user_agent=user_agent,
            last_seen_at=datetime.now(timezone.utc)  # Ghi nhận thời điểm tạo phiên
        )
        self.s.add(sess)  # Thêm phiên vào session
        await self.s.flush()  # Đẩy thay đổi lên DB để lấy id tự sinh
        return sess  # Trả về phiên vừa tạo