import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from packages.infra.db.models.ops.refresh_token import RefreshToken


class RefreshTokenRepo:
    """Lưu refresh token dưới dạng hash + metadata."""

    def __init__(self, session: AsyncSession) -> None:
        # Khởi tạo repository với một phiên làm việc async của SQLAlchemy
        self.s = session

    async def add(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        jti: UUID,
        family_id: UUID,
        token_hash: str,
        expires_at: datetime,
        commit: bool = False,
    ) -> None:
        """
        Thêm một refresh token mới vào database.
        - user_id: ID của người dùng sở hữu token.
        - session_id: ID phiên đăng nhập.
        - jti: ID duy nhất của token (JWT ID, dùng làm khóa chính).
        - family_id: ID nhóm token (dùng cho family refresh token).
        - token_hash: Hash của refresh token.
        - expires_at: Thời điểm hết hạn token.
        - commit: Nếu True thì commit thay đổi vào DB ngay.
        """
        rt = RefreshToken(
            id=jti,  # jti làm PK
            user_id=user_id,
            session_id=session_id,
            family_id=family_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
        )
        self.s.add(rt)  # Thêm đối tượng vào session
        await self.s.flush()  # Đẩy thay đổi lên DB (chưa commit)
        if commit:
            await self.s.commit()  # Commit nếu được yêu cầu

    async def get_by_jti(self, jti: UUID) -> Optional[RefreshToken]:
        """
        Lấy refresh token theo jti (JWT ID).
        - jti: ID duy nhất của token.
        Trả về đối tượng RefreshToken nếu tìm thấy, ngược lại trả về None.
        """
        stmt = select(RefreshToken).where(RefreshToken.id == jti)
        res = await self.s.execute(stmt)
        return res.scalars().first()  # Lấy bản ghi đầu tiên (nếu có)

    async def revoke(self, jti: UUID, commit: bool = True) -> None:
        """
        Đánh dấu một refresh token là đã bị thu hồi (revoked).
        - jti: ID duy nhất của token cần thu hồi.
        - commit: Nếu True thì commit thay đổi vào DB ngay.
        """
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == jti)
            .values(revoked=True)
        )
        await self.s.execute(stmt)  # Thực thi câu lệnh update
        if commit:
            await self.s.commit()  # Commit nếu được yêu cầu
