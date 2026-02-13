"""
游标分页工具 - 技术方案 4.1.1
避免深度分页性能问题，使用基于 ID 的游标分页替代 OFFSET
"""
from typing import TypeVar, Generic, Optional, List, Tuple
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta

T = TypeVar('T', bound=DeclarativeMeta)


class CursorPaginationResult(BaseModel, Generic[T]):
    """游标分页结果"""
    items: List[dict]  # 当前页数据
    next_cursor: Optional[str] = None  # 下一页游标
    has_more: bool = False  # 是否有更多数据
    total: Optional[int] = None  # 总数（可选）


class CursorPaginator:
    """
    游标分页器

    技术方案 4.1.1 - 使用游标分页替代 OFFSET 避免深度分页性能问题

    使用示例:
        paginator = CursorPaginator(Post, order_by=[Post.created_at.desc(), Post.id.desc()])

        # 第一页
        result = await paginator.paginate(db, limit=20)

        # 下一页
        result = await paginator.paginate(db, limit=20, cursor=result.next_cursor)
    """

    def __init__(
        self,
        model: type[T],
        order_by: List,  # 排序字段列表，最后一个是唯一字段(通常是id)
        *,
        filter_expr=None,
    ):
        """
        Args:
            model: SQLAlchemy 模型类
            order_by: 排序字段列表，例如 [Post.created_at.desc(), Post.id.desc()]
            filter_expr: 额外的过滤条件
        """
        self.model = model
        self.order_by = order_by
        self.filter_expr = filter_expr

    def _decode_cursor(self, cursor: str, convert_to_datetime: bool = True) -> Tuple:
        """
        解码游标

        游标格式: base64(json([value1, value2, ...]))
        其中 values 是排序字段的值

        Args:
            cursor: 游标字符串
            convert_to_datetime: 是否将 ISO 格式字符串转换为 datetime 对象
                               (用于 SQLAlchemy 比较操作)
        """
        import base64
        import json
        from datetime import datetime

        try:
            decoded = base64.b64decode(cursor.encode()).decode()
            values = json.loads(decoded)

            if not convert_to_datetime:
                return tuple(values)

            # Convert ISO format strings back to datetime for SQLAlchemy comparisons
            result = []
            for v in values:
                if isinstance(v, str) and len(v) >= 18:  # ISO datetime is at least 18 chars
                    try:
                        # Try to parse as ISO datetime
                        result.append(datetime.fromisoformat(v))
                    except (ValueError, AttributeError):
                        # Not a datetime, keep as is
                        result.append(v)
                else:
                    result.append(v)

            return tuple(result)
        except Exception:
            raise ValueError("Invalid cursor")

    def _encode_cursor(self, values: Tuple) -> str:
        """编码游标"""
        import base64
        import json

        # Convert datetime objects to ISO format strings
        serializable_values = []
        for v in values:
            if hasattr(v, 'isoformat'):
                # datetime object
                serializable_values.append(v.isoformat())
            else:
                serializable_values.append(v)

        encoded = json.dumps(serializable_values)
        return base64.b64encode(encoded.encode()).decode()

    def _build_conditions(self, cursor: Optional[str] = None):
        """
        构建分页条件

        技术方案 4.1.1 - 游标分页条件构建
        使用多个 OR 条件，每个条件检查排序字段是否小于游标值
        """
        from sqlalchemy import or_, and_

        if not cursor:
            return self.filter_expr

        values = self._decode_cursor(cursor)

        if len(values) != len(self.order_by):
            raise ValueError("Cursor does not match order_by columns")

        # 构建游标条件
        # 例如: (created_at < cursor_value) OR (created_at = cursor_value AND id < cursor_id)
        conditions = []
        equal_conditions = []

        for i, (order_col, cursor_val) in enumerate(zip(self.order_by, values)):
            # 判断是升序还是降序
            from sqlalchemy.sql.expression import UnaryExpression
            is_desc = (isinstance(order_col, UnaryExpression) and
                       hasattr(order_col, 'modifier') and
                       order_col.modifier.__name__ == 'desc_op')

            # 构建条件
            if is_desc:
                # 降序: 使用 <
                col_condition = order_col.element < cursor_val
            else:
                # 升序: 使用 >
                col_condition = order_col.element > cursor_val

            # 组合条件
            if equal_conditions:
                # 前面的字段相等，当前字段比较
                combined = and_(*equal_conditions, col_condition)
                conditions.append(combined)
            else:
                # 第一个字段直接比较
                conditions.append(col_condition)

            # 添加相等条件用于下一个字段
            equal_conditions.append(order_col.element == cursor_val)

        cursor_condition = or_(*conditions)

        # 组合游标条件和过滤条件
        if self.filter_expr:
            return and_(self.filter_expr, cursor_condition)

        return cursor_condition

    async def paginate(
        self,
        db: AsyncSession,
        *,
        limit: int = 20,
        cursor: Optional[str] = None,
        with_count: bool = False,
    ) -> CursorPaginationResult:
        """
        执行分页查询

        Args:
            db: 数据库会话
            limit: 每页数量
            cursor: 上一页返回的游标
            with_count: 是否返回总数（会额外执行 COUNT 查询）

        Returns:
            CursorPaginationResult
        """
        # 构建查询
        conditions = self._build_conditions(cursor)
        query = select(self.model)
        if conditions is not None:
            query = query.where(conditions)

        # 应用排序
        query = query.order_by(*self.order_by)

        # 应用 limit + 1 (用于判断是否有更多)
        query = query.limit(limit + 1)

        # 执行查询
        result = await db.execute(query)
        items = result.scalars().all()

        # 转换为字典列表
        items_dict = [
            {c.name: getattr(item, c.name) for c in item.__table__.columns}
            for item in items
        ]

        # 判断是否有更多
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]

        # 转换为字典列表
        items_dict = [
            {c.name: getattr(item, c.name) for c in item.__table__.columns}
            for item in items
        ]

        # 生成下一页游标
        next_cursor = None
        if has_more and items_dict:
            # 获取最后一条显示记录的排序字段值
            last_item = items[-1]
            cursor_values = tuple(
                getattr(last_item, col.element.key)
                for col in self.order_by
            )
            next_cursor = self._encode_cursor(cursor_values)

        # 可选: 获取总数
        total = None
        if with_count:
            base_query = select(self.model)
            if conditions is not None:
                base_query = base_query.where(conditions)
            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar()

        return CursorPaginationResult(
            items=items_dict,
            next_cursor=next_cursor,
            has_more=has_more,
            total=total,
        )


async def offset_paginate(
    db: AsyncSession,
    model: type[T],
    *,
    limit: int = 20,
    offset: int = 0,
    filter_expr=None,
    order_by: List = None,
    with_count: bool = True,
) -> dict:
    """
    传统 OFFSET 分页（向后兼容）

    对于深度分页建议使用 CursorPaginator

    Returns:
        {
            "items": List[dict],
            "total": int,
            "limit": int,
            "offset": int,
        }
    """
    # 构建查询
    query = select(model)
    if filter_expr:
        query = query.where(filter_expr)
    if order_by:
        query = query.order_by(*order_by)

    # 获取总数
    total = None
    if with_count:
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar()

    # 应用分页
    query = query.limit(limit).offset(offset)

    # 执行查询
    result = await db.execute(query)
    items = result.scalars().all()

    # 转换为字典列表
    items_dict = [
        {c.name: getattr(item, c.name) for c in item.__table__.columns}
        for item in items
    ]

    return {
        "items": items_dict,
        "total": total or 0,
        "limit": limit,
        "offset": offset,
    }
