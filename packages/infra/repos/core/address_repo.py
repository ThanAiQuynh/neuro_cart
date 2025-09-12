from typing import List, Optional
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from packages.infra.db.models.core.address import Address
from packages.infra.repos.base import SQLAlchemyRepository

class AddressRepo(SQLAlchemyRepository[Address]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Address)

    async def add(self, obj, *, commit: bool = False, refresh: bool = True) -> Address:
        # Nếu obj không phải ORM Address thì map sang entity
        if not isinstance(obj, Address):
            obj = Address(
                customer_id=obj.customer_id,
                line1=getattr(obj, "line1", None),
                line2=getattr(obj, "line2", None),
                city=getattr(obj, "city", None),
                state=getattr(obj, "state", None),
                postal_code=getattr(obj, "postal_code", None),
                country_code=getattr(obj, "country_code", None),
                is_default=getattr(obj, "is_default", False),
            )

        self.session.add(obj)
        await self.session.flush()

        if commit:
            await self.session.commit()
        if refresh:
            await self.session.refresh(obj)

        return obj

    async def list_by_customer(self, customer_id: int) -> List[Address]:
        """
        Lấy toàn bộ Address của một customer, 
        sắp xếp địa chỉ mặc định (is_default=True) lên trước, 
        rồi đến địa chỉ mới nhất (created_at desc).
        """
        stmt = (
            self.default_select()
            .where(Address.customer_id == customer_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        result = await self.session.execute(stmt)
        addresses = result.scalars().all()
        return list(addresses)

    async def default_for_customer(self, customer_id: int) -> Optional[Address]:
        """
        Lấy địa chỉ mặc định của một customer (nếu có).
        """
        stmt = (
            self.default_select()
            .where(Address.customer_id == customer_id, Address.is_default == True)  # noqa: E712
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def set_default(self, customer_id: int, address_id: int, *, commit: bool = False) -> None:
        """
        Đặt một địa chỉ cụ thể làm mặc định cho customer.
        - Bỏ cờ is_default của các địa chỉ khác.
        - Set is_default=True cho địa chỉ mới.
        """
        # 1. Bỏ cờ mặc định ở các địa chỉ hiện tại
        await self.session.execute(
            update(Address)
            .where(Address.customer_id == customer_id, Address.is_default == True)  # noqa: E712
            .values(is_default=False)
        )

        # 2. Set địa chỉ mới thành mặc định
        await self.session.execute(
            update(Address)
            .where(Address.customer_id == customer_id, Address.id == address_id)
            .values(is_default=True)
        )

        # 3. Commit nếu được yêu cầu
        if commit:
            await self.session.commit()
