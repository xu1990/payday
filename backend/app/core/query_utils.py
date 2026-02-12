"""
查询优化工具 - 提供常用的查询优化模式
"""
from typing import Type, TypeVar, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.base import Base

T = TypeVar('T', bound=Base)


class QueryHelper:
    """查询辅助类 - 提供常用的查询方法"""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        model: Type[T],
        entity_id: str,
        *,
        with_for_update: bool = False,
        eager_loads: Optional[List] = None,
    ) -> Optional[T]:
        """
        按 ID 查询单个实体

        Args:
            db: 数据库会话
            model: 模型类
            entity_id: 实体 ID
            with_for_update: 是否加行锁（用于更新）
            eager_loads: 预加载的关系列表

        Returns:
            实体或 None
        """
        query = select(model).where(model.id == entity_id)

        if eager_loads:
            for loader in eager_loads:
                query = query.options(loader)

        if with_for_update:
            query = query.with_for_update()

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_with_pagination(
        db: AsyncSession,
        model: Type[T],
        *,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[List] = None,
        order_by: Optional = None,
        eager_loads: Optional[List] = None,
    ) -> tuple[List[T], int]:
        """
        分页查询实体列表

        Args:
            db: 数据库会话
            model: 模型类
            limit: 每页数量
            offset: 偏移量
            filters: 过滤条件列表
            order_by: 排序条件
            eager_loads: 预加载的关系列表

        Returns:
            (实体列表, 总数)
        """
        from sqlalchemy import func

        # 构建基础查询
        count_query = select(func.count()).select_from(model)
        list_query = select(model)

        # 应用过滤条件
        if filters:
            for filter_condition in filters:
                count_query = count_query.where(filter_condition)
                list_query = list_query.where(filter_condition)

        # 应用预加载
        if eager_loads:
            for loader in eager_loads:
                list_query = list_query.options(loader)

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 应用排序和分页
        if order_by is not None:
            list_query = list_query.order_by(order_by)

        list_query = list_query.limit(limit).offset(offset)

        # 执行查询
        result = await db.execute(list_query)
        items = list(result.scalars().all())

        return items, total


async def get_or_404(
    db: AsyncSession,
    model: Type[T],
    entity_id: str,
    *,
    error_message: str = "资源不存在",
) -> T:
    """
    获取实体或抛出 404 异常

    Args:
        db: 数据库会话
        model: 模型类
        entity_id: 实体 ID
        error_message: 错误消息

    Returns:
        实体

    Raises:
        NotFoundException: 实体不存在
    """
    from app.core.exceptions import NotFoundException

    entity = await QueryHelper.get_by_id(db, model, entity_id)
    if not entity:
        raise NotFoundException(error_message)
    return entity
