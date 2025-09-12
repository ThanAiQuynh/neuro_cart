from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.infra.db.models.core.role import Role
from packages.infra.db.models.core.user import User
from packages.infra.db.models.core.user_role import UserRole
from packages.infra.repos.base import SQLAlchemyRepository
from packages.infra.repos.exceptions import NotFoundError


class UserRepo(SQLAlchemyRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def add(self, obj, *, commit: bool = False, refresh: bool = True) -> User:
        if not isinstance(obj, User):
            obj = User(
                email=obj.email,
                password_hash=obj.password_hash,
                full_name=getattr(obj, "full_name", None),
                phone=getattr(obj, "phone", None),
                is_active=getattr(obj, "is_active", True),
            )

        self.session.add(obj)
        await self.session.flush()

        if commit:
            await self.session.commit()
        if refresh:
            await self.session.refresh(obj)
        return obj
    
    async def search_by_email(self, email: str, *, with_deleted: bool = False) -> User:
        # 1. Tạo câu query cơ bản
        #    Giả sử self.default_select(with_deleted) trả về một object `select(User)` 
        #    đã được filter điều kiện deleted nếu cần
        stmt = self.default_select(with_deleted).where(User.email == email)
        # 2. Thực thi query bằng async session
        #    `.execute(stmt)` trả về Result object
        result = await self.session.execute(stmt)
        # 3. Lấy ra object User đầu tiên từ Result
        #    `.scalars()` để map sang các object User thay vì Row tuple
        #    `.first()` lấy phần tử đầu tiên hoặc None nếu không có
        obj = result.scalars().first()
        # 4. Nếu không có user nào thì raise NotFoundError
        if not obj:
            raise NotFoundError(f"User with email {email} not found")
        # 5. Trả về User object
        return obj
    
    async def search(self, q: str, limit: int = 20) -> list[User]:
        # 1. Tạo câu query cơ bản
        #    - default_select() trả về select(User).where(User.is_deleted == False) nếu có
        #    - ilike: so khớp không phân biệt hoa/thường
        stmt = (
            self.default_select()
            .where(
                or_(
                    User.email.ilike(f"%{q}%"),
                    User.full_name.ilike(f"%{q}%"),
                )
            )
            .limit(limit)
        )
        # 2. Thực thi query (async)
        result = await self.session.execute(stmt)
        # 3. Lấy ra toàn bộ User object từ kết quả
        #    - scalars(): ánh xạ sang object User thay vì tuple
        #    - all(): lấy toàn bộ record
        users = result.scalars().all()
        # 4. Trả về list user (ép sang list cho chắc)
        return list(users)
    
    async def activate(self, user: User, *, commit: bool = False) -> User:
        # 1. Cập nhật trạng thái user
        user.is_active = True
        # 2. Flush để đẩy thay đổi xuống DB trong transaction hiện tại
        #    nhưng chưa commit (chưa kết thúc transaction).
        await self.session.flush()
        # 3. Nếu muốn commit ngay thì commit luôn
        if commit:
            await self.session.commit()
        # 4. Trả về object user sau khi cập nhật
        return user
    
    async def deactivate(self, user: User, *, commit: bool = False) -> User:
        """
        Vô hiệu hóa User (set is_active=False).
        """
        user.is_active = False
        await self.session.flush()

        if commit:
            await self.session.commit()

        return user
    
    async def add_role(self, user: User, role_code: str, *, commit: bool = False) -> None:
        """
        Thêm role vào user (nếu role tồn tại và chưa được gán).
        """
        # 1. Query role theo role_code
        result = await self.session.execute(
            select(Role).where(Role.code == role_code)
        )
        role = result.scalars().first()

        # 2. Nếu không tìm thấy role thì báo lỗi
        if not role:
            raise NotFoundError(f"Role {role_code} not found")

        # 3. Nếu user chưa có role này thì thêm vào
        if role not in user.roles:
            user.roles.append(role)
            await self.session.flush()

            if commit:
                await self.session.commit()

    async def remove_role(self, user: User, role_code: str, *, commit: bool = False) -> None:
        """
        Xóa role khỏi user (nếu role tồn tại và user đang có role đó).
        """
        result = await self.session.execute(
            select(Role).where(Role.code == role_code)
        )
        role = result.scalars().first()

        # Nếu không có role thì thôi, không làm gì
        if not role:
            return

        # Nếu user có role này thì remove
        if role in user.roles:
            user.roles.remove(role)
            await self.session.flush()

            if commit:
                await self.session.commit()

    async def list_users_with_role(self, role_code: str, limit: int = 100) -> list[User]:
        """
        Lấy danh sách user có role cụ thể.
        """
        stmt = (
            self.default_select()
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.code == role_code)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        users = result.scalars().all()

        return list(users)