"""
会员接口 - Sprint 3.5 会员订单、权益验证
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.membership import MembershipOrder
from app.schemas.membership import MembershipListResponse, MembershipOrderCreate
from app.services.membership_service import (
    cancel_order,
    create_order,
    get_active_membership,
    list_memberships,
    verify_membership_benefits,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/membership", tags=["membership"])


@router.get("", response_model=MembershipListResponse)
async def list_memberships_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有可用会员套餐"""
    memberships = await list_memberships(db)
    return MembershipListResponse(items=memberships)


@router.post("/order", response_model=dict)
async def create_order_endpoint(
    body: MembershipOrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建会员订单"""
    order = await create_order(
        db,
        current_user.id,
        body.membership_id,
        body.amount,
        body.payment_method,
        body.transaction_id,
    )
    return {"id": order.id, "status": "pending", "message": "订单创建成功"}


@router.get("/my-orders")
async def list_my_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的会员订单列表"""
    orders = await get_my_orders(db, current_user.id)
    return {"items": orders}


@router.get("/active")
async def get_active_membership_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前激活的会员"""
    active = await get_active_membership(db, current_user.id)
    return active if active else {}


@router.post("/order/{order_id}/cancel")
async def cancel_order_endpoint(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消会员订单"""
    try:
        await cancel_order(db, order_id, current_user.id)
        return {"success": True, "message": "订单已取消"}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))
