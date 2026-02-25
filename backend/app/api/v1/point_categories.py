"""
积分商品分类接口 - 管理后台
Sprint 4.7 - 商品兑换系统
"""
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import success_response
from app.models.point_category import PointCategory
from app.models.user import User
from app.services.point_category_service import (create_category, delete_category, get_category,
                                                 get_category_tree, list_categories,
                                                 update_category)
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin/point-categories", tags=["admin-point-categories"])


# ==================== Request/Response Schemas ====================

class CategoryCreate(BaseModel):
    """创建分类请求"""
    name: str = Field(..., max_length=50, description="分类名称")
    level: int = Field(..., ge=1, le=3, description="层级(1/2/3)")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[str] = Field(None, description="父分类ID")
    icon_url: Optional[str] = Field(None, max_length=500, description="图标URL")
    banner_url: Optional[str] = Field(None, max_length=500, description="横幅URL")
    sort_order: int = Field(0, description="排序权重")
    is_active: bool = Field(True, description="是否启用")


class CategoryUpdate(BaseModel):
    """更新分类请求"""
    name: Optional[str] = Field(None, max_length=50, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    icon_url: Optional[str] = Field(None, max_length=500, description="图标URL")
    banner_url: Optional[str] = Field(None, max_length=500, description="横幅URL")
    sort_order: Optional[int] = Field(None, description="排序权重")
    is_active: Optional[bool] = Field(None, description="是否启用")


def category_to_dict(category: PointCategory) -> dict:
    """将分类对象转换为字典"""
    return {
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
    }


# ==================== API Endpoints ====================

@router.post("")
async def create_point_category(
    data: CategoryCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建积分商品分类"""
    category = await create_category(
        db,
        name=data.name,
        level=data.level,
        description=data.description,
        parent_id=data.parent_id,
        icon_url=data.icon_url,
        banner_url=data.banner_url,
        sort_order=data.sort_order,
        is_active=data.is_active,
    )

    return success_response(
        data=category_to_dict(category),
        message="创建分类成功"
    )


@router.get("")
async def list_point_categories(
    active_only: bool = Query(False, description="是否只返回启用的分类"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取积分商品分类列表（平铺）"""
    # Get all categories by passing a special marker
    # We'll query directly to get all categories
    from sqlalchemy import select

    query = select(PointCategory)

    if active_only:
        query = query.where(PointCategory.is_active == True)

    query = query.order_by(
        PointCategory.sort_order.desc(),
        PointCategory.created_at.desc()
    )

    result = await db.execute(query)
    categories = result.scalars().all()

    # Convert all categories to dict
    categories_data = [category_to_dict(cat) for cat in categories]

    return success_response(
        data=categories_data,
        message="获取分类列表成功"
    )


@router.get("/tree")
async def get_point_category_tree(
    active_only: bool = Query(True, description="是否只返回启用的分类"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取积分商品分类树（层级结构）"""
    tree = await get_category_tree(db, active_only=active_only)

    return success_response(
        data=tree,
        message="获取分类树成功"
    )


@router.get("/{category_id}")
async def get_point_category(
    category_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个分类详情"""
    category = await get_category(db, category_id)

    return success_response(
        data=category_to_dict(category),
        message="获取分类成功"
    )


@router.put("/{category_id}")
async def update_point_category(
    category_id: str,
    data: CategoryUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新积分商品分类"""
    # 只传递非None的字段
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    category = await update_category(db, category_id, **update_data)

    return success_response(
        data=category_to_dict(category),
        message="更新分类成功"
    )


@router.delete("/{category_id}")
async def delete_point_category(
    category_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除积分商品分类"""
    await delete_category(db, category_id)

    return success_response(
        data={"deleted": True},
        message="删除分类成功"
    )
