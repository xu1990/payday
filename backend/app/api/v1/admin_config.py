"""
会员与主题配置接口 - 管理后台
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.models.user import User
from app.models.membership import Membership, AppTheme, MembershipOrder
from app.schemas.membership import MembershipCreate, MembershipResponse, MembershipListResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/admin/config", tags=["admin-config"])


# ==================== 主题管理 ====================

class ThemeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    preview_image: Optional[str] = Field(None, max_length=500)
    config: Optional[str] = Field(None)
    is_premium: bool = False
    sort_order: int = Field(0, ge=0)


class ThemeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    preview_image: Optional[str] = Field(None, max_length=500)
    config: Optional[str] = None
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class ThemeResponse(BaseModel):
    id: str
    name: str
    code: str
    preview_image: Optional[str]
    config: Optional[str]
    is_premium: bool
    is_active: bool
    sort_order: int
    created_at: str

    class Config:
        from_attributes = True


@router.get("/themes", response_model=list[ThemeResponse])
async def list_themes(
    active_only: bool = Query(False),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取主题列表。"""
    from sqlalchemy import select

    q = select(AppTheme)
    if active_only:
        q = q.where(AppTheme.is_active == True)
    q = q.order_by(AppTheme.sort_order.desc(), AppTheme.created_at.desc())
    result = await db.execute(q)
    themes = list(result.scalars().all())
    return [ThemeResponse.model_validate(t) for t in themes]


@router.post("/themes", response_model=ThemeResponse)
async def create_theme(
    data: ThemeCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建主题。"""
    theme = AppTheme(**data.model_dump())
    db.add(theme)
    await db.flush()
    await db.refresh(theme)
    return ThemeResponse.model_validate(theme)


@router.put("/themes/{theme_id}", response_model=ThemeResponse)
async def update_theme(
    theme_id: str,
    data: ThemeUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新主题。"""
    from sqlalchemy import select, update

    result = await db.execute(select(AppTheme).where(AppTheme.id == theme_id))
    theme = result.scalar_one_or_none()
    if not theme:
        from fastapi import HTTPException

        raise NotFoundException("资源不存在")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    await db.execute(
        update(AppTheme).where(AppTheme.id == theme_id).values(**update_data)
    )
    await db.commit()
    await db.refresh(theme)
    return ThemeResponse.model_validate(theme)


@router.delete("/themes/{theme_id}")
async def delete_theme(
    theme_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除主题。"""
    from sqlalchemy import delete

    result = await db.execute(delete(AppTheme).where(AppTheme.id == theme_id))
    await db.commit()
    return {"deleted": result.rowcount > 0}


# ==================== 会员套餐管理 ====================

class MembershipListResponse(BaseModel):
    items: list[MembershipResponse]
    total: int


@router.get("/memberships", response_model=MembershipListResponse)
async def list_memberships(
    active_only: bool = Query(False),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取会员套餐列表。"""
    from sqlalchemy import select, func

    q = select(Membership)
    if active_only:
        q = q.where(Membership.is_active == 1)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(Membership.sort_order.desc(), Membership.created_at.desc())
    result = await db.execute(q)
    items = list(result.scalars().all())
    return MembershipListResponse(
        items=[MembershipResponse.model_validate(m) for m in items], total=total
    )


@router.post("/memberships", response_model=MembershipResponse)
async def create_membership(
    data: MembershipCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建会员套餐。"""
    membership = Membership(**data.model_dump())
    db.add(membership)
    await db.flush()
    await db.refresh(membership)
    return MembershipResponse.model_validate(membership)


@router.put("/memberships/{membership_id}", response_model=MembershipResponse)
async def update_membership(
    membership_id: str,
    data: MembershipCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新会员套餐。"""
    from sqlalchemy import select, update

    result = await db.execute(
        select(Membership).where(Membership.id == membership_id)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        from fastapi import HTTPException

        raise NotFoundException("资源不存在")

    update_data = data.model_dump()
    await db.execute(
        update(Membership)
        .where(Membership.id == membership_id)
        .values(**update_data)
    )
    await db.commit()
    await db.refresh(membership)
    return MembershipResponse.model_validate(membership)


@router.delete("/memberships/{membership_id}")
async def delete_membership(
    membership_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除会员套餐。"""
    from sqlalchemy import delete

    result = await db.execute(
        delete(Membership).where(Membership.id == membership_id)
    )
    await db.commit()
    return {"deleted": result.rowcount > 0}


# ==================== 会员订单管理 ====================

class OrderListResponse(BaseModel):
    items: list
    total: int


class OrderStatusUpdate(BaseModel):
    status: str  # pending | paid | cancelled | refunded


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取会员订单列表。"""
    from sqlalchemy import select, func

    q = select(MembershipOrder)
    # 关联会员套餐名称
    q = q.join(Membership, MembershipOrder.membership_id == Membership.id)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(MembershipOrder.created_at.desc())
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    orders = list(result.scalars().all())

    # 构建响应，包含套餐名称
    items = []
    for order in orders:
        # 获取套餐名称
        membership_result = await db.execute(
            select(Membership).where(Membership.id == order.membership_id)
        )
        membership = membership_result.scalar_one_or_none()

        item = {
            "id": order.id,
            "user_id": order.user_id,
            "membership_id": order.membership_id,
            "membership_name": membership.name if membership else "未知套餐",
            "amount": float(order.amount),
            "status": order.status,
            "payment_method": order.payment_method,
            "transaction_id": order.transaction_id,
            "start_date": order.start_date.isoformat() if order.start_date else None,
            "end_date": order.end_date.isoformat() if order.end_date else None,
            "auto_renew": bool(order.auto_renew),
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
        items.append(item)

    return OrderListResponse(items=items, total=total)


@router.put("/orders/{order_id}")
async def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新订单状态。"""
    from sqlalchemy import select, update

    result = await db.execute(
        select(MembershipOrder).where(MembershipOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        from fastapi import HTTPException
        raise NotFoundException("资源不存在")

    await db.execute(
        update(MembershipOrder)
        .where(MembershipOrder.id == order_id)
        .values(status=data.status)
    )
    await db.commit()
    return {"updated": True}
