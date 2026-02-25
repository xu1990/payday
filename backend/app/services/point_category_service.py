"""
积分分类服务 - Sprint 4.7 商品兑换系统
"""
from typing import Any, Dict, List, Optional

from app.core.exceptions import NotFoundException, ValidationException
from app.models.point_category import PointCategory
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_category(
    db: AsyncSession,
    name: str,
    level: int,
    description: Optional[str] = None,
    parent_id: Optional[str] = None,
    icon_url: Optional[str] = None,
    banner_url: Optional[str] = None,
    sort_order: int = 0,
    is_active: bool = True,
) -> PointCategory:
    """
    创建分类

    Args:
        db: 数据库会话
        name: 分类名称
        level: 层级 (1/2/3)
        description: 分类描述
        parent_id: 父分类ID
        icon_url: 图标URL
        banner_url: 横幅URL
        sort_order: 排序权重
        is_active: 是否启用

    Returns:
        创建的分类对象
    """
    # 如果有父分类，验证父分类存在
    if parent_id:
        result = await db.execute(
            select(PointCategory).where(PointCategory.id == parent_id)
        )
        parent = result.scalar_one_or_none()
        if not parent:
            raise NotFoundException("父分类不存在")

    category = PointCategory(
        name=name,
        level=level,
        description=description,
        parent_id=parent_id,
        icon_url=icon_url,
        banner_url=banner_url,
        sort_order=sort_order,
        is_active=is_active,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def get_category(
    db: AsyncSession,
    category_id: str
) -> PointCategory:
    """
    获取分类详情

    Args:
        db: 数据库会话
        category_id: 分类ID

    Returns:
        分类对象

    Raises:
        NotFoundException: 分类不存在
    """
    result = await db.execute(
        select(PointCategory).where(PointCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise NotFoundException("分类不存在")

    return category


async def list_categories(
    db: AsyncSession,
    parent_id: Optional[str] = None,
    active_only: bool = True,
) -> List[PointCategory]:
    """
    获取分类列表

    Args:
        db: 数据库会话
        parent_id: 父分类ID（None表示获取顶级分类）
        active_only: 是否只返回启用的分类

    Returns:
        分类列表
    """
    query = select(PointCategory)

    if parent_id is not None:
        query = query.where(PointCategory.parent_id == parent_id)
    else:
        query = query.where(PointCategory.parent_id.is_(None))

    if active_only:
        query = query.where(PointCategory.is_active == True)

    query = query.order_by(
        PointCategory.sort_order.desc(),
        PointCategory.created_at.desc()
    )

    result = await db.execute(query)
    return list(result.scalars().all())


def _build_category_tree(
    categories: List[PointCategory],
    parent_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    递归构建分类树

    Args:
        categories: 所有分类列表
        parent_id: 父分类ID

    Returns:
        分类树列表
    """
    tree = []
    for category in categories:
        if category.parent_id == parent_id:
            node = {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "parent_id": category.parent_id,
                "icon_url": category.icon_url,
                "banner_url": category.banner_url,
                "level": category.level,
                "sort_order": category.sort_order,
                "is_active": bool(category.is_active),
                "created_at": category.created_at.isoformat() if category.created_at else None,
                "updated_at": category.updated_at.isoformat() if category.updated_at else None,
                "children": _build_category_tree(categories, category.id),
            }
            tree.append(node)
    return tree


async def get_category_tree(
    db: AsyncSession,
    active_only: bool = True,
) -> List[Dict[str, Any]]:
    """
    获取分类树（层级结构）

    Args:
        db: 数据库会话
        active_only: 是否只返回启用的分类

    Returns:
        分类树列表
    """
    # 获取所有分类
    query = select(PointCategory)

    if active_only:
        query = query.where(PointCategory.is_active == True)

    query = query.order_by(
        PointCategory.sort_order.desc(),
        PointCategory.created_at.desc()
    )

    result = await db.execute(query)
    categories = list(result.scalars().all())

    # 构建树形结构
    return _build_category_tree(categories)


async def update_category(
    db: AsyncSession,
    category_id: str,
    **kwargs
) -> PointCategory:
    """
    更新分类

    Args:
        db: 数据库会话
        category_id: 分类ID
        **kwargs: 要更新的字段

    Returns:
        更新后的分类对象

    Raises:
        NotFoundException: 分类不存在
    """
    result = await db.execute(
        select(PointCategory).where(PointCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise NotFoundException("分类不存在")

    # 更新字段
    for key, value in kwargs.items():
        if hasattr(category, key) and value is not None:
            setattr(category, key, value)

    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(
    db: AsyncSession,
    category_id: str
) -> None:
    """
    删除分类

    Args:
        db: 数据库会话
        category_id: 分类ID

    Raises:
        NotFoundException: 分类不存在
        ValidationException: 分类有子分类，无法删除
    """
    # 检查分类是否存在
    result = await db.execute(
        select(PointCategory).where(PointCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise NotFoundException("分类不存在")

    # 检查是否有子分类
    children_result = await db.execute(
        select(PointCategory).where(PointCategory.parent_id == category_id)
    )
    children = children_result.scalars().all()

    if children:
        raise ValidationException("该分类下有子分类，无法删除")

    # 删除分类
    await db.delete(category)
    await db.commit()
