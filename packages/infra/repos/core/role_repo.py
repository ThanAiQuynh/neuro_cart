from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.infra.db.models.core.role import Role
from packages.infra.repos.base import SQLAlchemyRepository
from packages.infra.repos.exceptions import NotFoundError

class RoleRepo(SQLAlchemyRepository[Role]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Role)

    async def by_code(self, code: str) -> Role:
        """
        Lấy Role theo code.
        """
        stmt = self.default_select().where(Role.code == code)
        result = await self.session.execute(stmt)
        obj = result.scalars().first()

        if not obj:
            raise NotFoundError(f"Role {code} not found")
        return obj

    async def ensure(self, code: str, name: Optional[str] = None, *, commit: bool = False) -> Role:
        """
        Đảm bảo role tồn tại: 
        - Nếu có thì trả về role đó.
        - Nếu chưa có thì tạo mới.

        Returns:
            Role: Role đã tồn tại hoặc mới tạo.
        """
        # 1. Kiểm tra role đã tồn tại chưa
        result = await self.session.execute(select(Role).where(Role.code == code))
        obj = result.scalars().first()

        if obj:
            return obj

        # 2. Nếu chưa có thì tạo mới
        obj = Role(code=code, name=name or code.title())
        self.session.add(obj)
        await self.session.flush()

        if commit:
            await self.session.commit()

        return obj
