from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from packages.infra.db.models.core.address import Address
from packages.infra.db.models.core.customer import Customer
from packages.infra.repos.base import SQLAlchemyRepository
from packages.infra.repos.exceptions import NotFoundError

class CustomerRepo(SQLAlchemyRepository[Customer]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Customer)

    async def by_user_id(self, user_id: int) -> Customer:
        """
        Lấy Customer theo user_id.

        Args:
            user_id (int): id của User liên kết.

        Returns:
            Customer: object Customer.

        Raises:
            NotFoundError: nếu không tìm thấy.
        """
        stmt = self.default_select().where(Customer.user_id == user_id)
        result = await self.session.execute(stmt)
        obj = result.scalars().first()

        if not obj:
            raise NotFoundError(f"Customer for user_id {user_id} not found")

        return obj

    async def ensure_for_user(self, user_id: int, tier: str = "standard", *, commit: bool = False) -> Customer:
        """
        Đảm bảo user có Customer record:
        - Nếu đã tồn tại thì trả về luôn.
        - Nếu chưa có thì tạo mới.

        Args:
            user_id (int): id của User.
            tier (str): gói (tier) của Customer, mặc định = "standard".
            commit (bool): nếu True thì commit ngay sau khi thêm.

        Returns:
            Customer: object Customer.
        """
        result = await self.session.execute(
            select(Customer).where(Customer.user_id == user_id)
        )
        obj = result.scalars().first()

        if obj:
            return obj

        # Tạo mới nếu chưa có
        obj = Customer(user_id=user_id, tier=tier)
        self.session.add(obj)
        await self.session.flush()

        if commit:
            await self.session.commit()

        return obj

    async def addresses(self, customer_id: int) -> List[Address]:
        """
        Lấy danh sách Address của customer, 
        sắp xếp ưu tiên địa chỉ mặc định (is_default=True) trước,
        sau đó theo ngày tạo mới nhất.

        Args:
            customer_id (int): id của Customer.

        Returns:
            list[Address]: danh sách địa chỉ.
        """
        stmt = (
            select(Address)
            .where(Address.customer_id == customer_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )

        result = await self.session.execute(stmt)
        addresses = result.scalars().all()

        return list(addresses)
