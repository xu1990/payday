"""
物流公司管理接口 - Courier Management API
管理后台 - 物流公司CRUD操作
"""
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import success_response
from app.models.shipping import CourierCompany
from app.models.user import User
from app.schemas.shipping import CourierCreate, CourierUpdate
from app.services.courier_service import (create_courier, delete_courier, get_courier,
                                          list_couriers, update_courier)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin/couriers", tags=["admin-couriers"])


def courier_to_dict(courier: CourierCompany) -> dict:
    """将物流公司对象转换为字典"""
    return {
        "id": courier.id,
        "name": courier.name,
        "code": courier.code,
        "website": courier.website,
        "tracking_url": courier.tracking_url,
        "supports_cod": bool(courier.supports_cod),
        "supports_cold_chain": bool(courier.supports_cold_chain),
        "sort_order": courier.sort_order,
        "is_active": bool(courier.is_active),
        "created_at": courier.created_at.isoformat() if courier.created_at else None,
    }


# ==================== API Endpoints ====================

@router.post("")
async def create_courier_endpoint(
    data: CourierCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建物流公司"""
    courier = await create_courier(
        db,
        name=data.name,
        code=data.code,
        website=data.website,
        tracking_url=data.tracking_url,
        supports_cod=data.supports_cod,
        supports_cold_chain=data.supports_cold_chain,
        sort_order=data.sort_order,
        is_active=data.is_active,
    )

    return success_response(
        data=courier_to_dict(courier),
        message="创建物流公司成功"
    )


@router.get("")
async def list_couriers_endpoint(
    active_only: bool = Query(False, description="是否只返回启用的物流公司"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取物流公司列表"""
    couriers = await list_couriers(db, active_only=active_only)

    return success_response(
        data=[courier_to_dict(c) for c in couriers],
        message="获取物流公司列表成功"
    )


@router.get("/active")
async def list_active_couriers_endpoint(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取启用的物流公司列表（用于下拉选择）"""
    couriers = await list_couriers(db, active_only=True)

    return success_response(
        data=[courier_to_dict(c) for c in couriers],
        message="获取启用的物流公司列表成功"
    )


@router.get("/{courier_id}")
async def get_courier_endpoint(
    courier_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个物流公司详情"""
    courier = await get_courier(db, courier_id)

    return success_response(
        data=courier_to_dict(courier),
        message="获取物流公司成功"
    )


@router.put("/{courier_id}")
async def update_courier_endpoint(
    courier_id: str,
    data: CourierUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新物流公司信息"""
    # 只传递非None的字段
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    courier = await update_courier(db, courier_id, **update_data)

    return success_response(
        data=courier_to_dict(courier),
        message="更新物流公司成功"
    )


@router.delete("/{courier_id}")
async def delete_courier_endpoint(
    courier_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除物流公司"""
    await delete_courier(db, courier_id)

    return success_response(
        data={"deleted": True},
        message="删除物流公司成功"
    )
