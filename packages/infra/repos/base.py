from __future__ import annotations
from typing import Any, Callable, Generic, Optional, Sequence, Type, TypeVar, List
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from packages.infra.db.models.base import Base
from packages.infra.repos.exceptions import NotFoundError, NotSoftDeletable
from packages.infra.repos.types import Page, PageParams

ModelT = TypeVar("ModelT", bound=Base)


class SQLAlchemyRepository(Generic[ModelT]):
    """Generic async repository for SQLAlchemy 2.0
    - Hỗ trợ soft delete (deleted_at)
    - Hỗ trợ phân trang
    - Dùng AsyncSession thay vì Session
    """

    def __init__(self, session: AsyncSession, model: Type[ModelT]):
        self.session = session
        self.model = model
        self._page_size_cap = 200
        self.base_query_hook: Optional[Callable[[Select], Select]] = None

    # ----------------------
    # Helpers nội bộ
    # ----------------------
    def _has_soft_delete(self) -> bool:
        """Check xem model có cột `deleted_at` không (hỗ trợ soft delete)."""
        return hasattr(self.model, "deleted_at")

    def _apply_live_filter(self, stmt: Select, with_deleted: bool) -> Select:
        """Nếu model hỗ trợ soft delete → lọc bỏ record đã xóa (deleted_at != NULL)."""
        if not with_deleted and self._has_soft_delete():
            stmt = stmt.where(getattr(self.model, "deleted_at") == None)  # noqa: E711
        return stmt

    def _apply_filters(self, stmt: Select, filters: Optional[Sequence[ColumnElement[Any]]] = None) -> Select:
        """Thêm filters vào query nếu có."""
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        return stmt

    def _apply_order(self, stmt: Select, order_by: Optional[Sequence[Any]] = None) -> Select:
        """Thêm order_by nếu có."""
        if order_by:
            stmt = stmt.order_by(*order_by)
        return stmt

    def _apply_base_hook(self, stmt: Select) -> Select:
        """Hook cho phép custom base query trước khi chạy."""
        if self.base_query_hook is not None:
            return self.base_query_hook(stmt)
        return stmt

    def default_select(self, with_deleted: bool = False) -> Select:
        """Tạo câu query mặc định: select model + filter deleted."""
        stmt: Select = select(self.model)
        stmt = self._apply_live_filter(stmt, with_deleted)
        stmt = self._apply_base_hook(stmt)
        return stmt

    # ----------------------
    # CRUD methods
    # ----------------------
    async def get(self, id: Any, *, with_deleted: bool = False) -> ModelT:
        """Lấy object theo id. Nếu không tìm thấy → raise NotFoundError."""
        stmt = self.default_select(with_deleted).where(self.model.id == id)
        result = await self.session.execute(stmt)
        obj = result.scalars().first()
        if obj is None:
            raise NotFoundError(f"{self.model.__name__}({id}) not found")
        return obj

    async def get_optional(self, id: Any, *, with_deleted: bool = False) -> Optional[ModelT]:
        """Lấy object theo id, nếu không có thì return None."""
        stmt = self.default_select(with_deleted).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_one(self, *, filters: Sequence[ColumnElement[Any]], with_deleted: bool = False) -> ModelT:
        """Lấy object theo filters. Nếu không tìm thấy → raise NotFoundError."""
        stmt = self.default_select(with_deleted)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt)
        obj = result.scalars().first()
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} not found for given filters")
        return obj

    async def list(
        self,
        *,
        filters: Optional[Sequence[ColumnElement[Any]]] = None,
        order_by: Optional[Sequence[Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        with_deleted: bool = False,
    ) -> List[ModelT]:
        """Lấy danh sách object theo filter/order/limit/offset."""
        stmt = self.default_select(with_deleted)
        stmt = self._apply_filters(stmt, filters)
        stmt = self._apply_order(stmt, order_by)
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def paginate(
        self,
        params: PageParams,
        *,
        filters: Optional[Sequence[ColumnElement[Any]]] = None,
        order_by: Optional[Sequence[Any]] = None,
        with_deleted: bool = False,
    ) -> Page[ModelT]:
        """Phân trang: trả về Page object (items, total, page, size)."""
        count_stmt = select(func.count()).select_from(self.default_select(with_deleted).subquery())
        count_stmt = self._apply_filters(count_stmt, filters)
        total = (await self.session.execute(count_stmt)).scalar_one()

        size = min(max(params.size, 1), self._page_size_cap)
        page = max(params.page, 1)
        offset = (page - 1) * size

        items = await self.list(
            filters=filters,
            order_by=order_by,
            limit=size,
            offset=offset,
            with_deleted=with_deleted,
        )
        return Page(items=items, total=total, page=page, size=size)

    async def add(self, obj: ModelT, *, commit: bool = False, refresh: bool = True) -> ModelT:
        """Thêm 1 object vào DB."""
        self.session.add(obj)
        await self.session.flush()
        if commit:
            await self.session.commit()
        if refresh:
            await self.session.refresh(obj)
        return obj

    async def add_many(self, objs, *, commit: bool = False):
        """Thêm nhiều object 1 lần."""
        self.session.add_all(list(objs))
        await self.session.flush()
        if commit:
            await self.session.commit()
        return list(objs)

    async def update(self, obj: ModelT, data: dict[str, Any], *, commit: bool = False, refresh: bool = True) -> ModelT:
        """Update object theo dict data."""
        for k, v in data.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        await self.session.flush()
        if commit:
            await self.session.commit()
        if refresh:
            await self.session.refresh(obj)
        return obj

    async def soft_delete(self, obj: ModelT, *, commit: bool = False) -> None:
        """Soft delete: set deleted_at = now()."""
        if not self._has_soft_delete():
            raise NotSoftDeletable(f"{self.model.__name__} does not support soft delete (missing deleted_at)")
        setattr(obj, "deleted_at", func.now())
        await self.session.flush()
        if commit:
            await self.session.commit()

    async def restore(self, obj: ModelT, *, commit: bool = False) -> None:
        """Khôi phục object đã soft delete: set deleted_at = None."""
        if not self._has_soft_delete():
            raise NotSoftDeletable(f"{self.model.__name__} does not support soft delete (missing deleted_at)")
        setattr(obj, "deleted_at", None)
        await self.session.flush()
        if commit:
            await self.session.commit()

    async def hard_delete(self, obj: ModelT, *, commit: bool = False) -> None:
        """Xóa hẳn object khỏi DB."""
        await self.session.delete(obj)
        await self.session.flush()
        if commit:
            await self.session.commit()

    async def exists(self, *, filters: Sequence[ColumnElement[Any]], with_deleted: bool = False) -> bool:
        """Check xem có object nào match filter không."""
        stmt = self.default_select(with_deleted)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt.limit(1))
        return result.first() is not None

    async def count(self, *, filters: Optional[Sequence[ColumnElement[Any]]] = None, with_deleted: bool = False) -> int:
        """Đếm số lượng object match filter."""
        stmt = select(func.count()).select_from(self.default_select(with_deleted).subquery())
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())
