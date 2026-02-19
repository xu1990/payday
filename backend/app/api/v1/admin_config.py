"""
会员与主题配置接口 - 管理后台
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import success_response, NotFoundException
from app.models.user import User
from app.models.membership import Membership, AppTheme, MembershipOrder
from app.schemas.membership import MembershipCreate, MembershipResponse

router = APIRouter(prefix="/admin/config", tags=["admin-config"])


# ==================== 主题管理 ====================

class ThemeCreate(BaseModel):
    name: str
    code: str
    preview_image: Optional[str] = None
    config: Optional[str] = None
    is_premium: bool = False
    sort_order: int = 0


class ThemeUpdate(BaseModel):
    name: Optional[str] = None
    preview_image: Optional[str] = None
    config: Optional[str] = None
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("/themes")
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

    items = []
    for t in themes:
        items.append({
            "id": t.id,
            "name": t.name,
            "code": t.code,
            "preview_image": t.preview_image,
            "config": t.config,
            "is_premium": bool(t.is_premium),
            "is_active": bool(t.is_active),
            "sort_order": t.sort_order,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return success_response(data=items, message="获取主题列表成功")


@router.post("/themes")
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

    result = {
        "id": theme.id,
        "name": theme.name,
        "code": theme.code,
        "preview_image": theme.preview_image,
        "config": theme.config,
        "is_premium": bool(theme.is_premium),
        "is_active": bool(theme.is_active),
        "sort_order": theme.sort_order,
        "created_at": theme.created_at.isoformat() if theme.created_at else None,
    }

    return success_response(data=result, message="创建主题成功")


@router.put("/themes/{theme_id}")
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
        raise NotFoundException("资源不存在")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    await db.execute(
        update(AppTheme).where(AppTheme.id == theme_id).values(**update_data)
    )
    await db.commit()
    await db.refresh(theme)

    response_data = {
        "id": theme.id,
        "name": theme.name,
        "code": theme.code,
        "preview_image": theme.preview_image,
        "config": theme.config,
        "is_premium": bool(theme.is_premium),
        "is_active": bool(theme.is_active),
        "sort_order": theme.sort_order,
        "created_at": theme.created_at.isoformat() if theme.created_at else None,
    }

    return success_response(data=response_data, message="更新主题成功")


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
    return success_response(data={"deleted": result.rowcount > 0}, message="删除主题成功")


# ==================== 会员套餐管理 ====================

@router.get("/memberships")
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

    items_data = [MembershipResponse.model_validate(m).model_dump() for m in items]

    return success_response(
        data={"items": items_data, "total": total},
        message="获取会员套餐列表成功"
    )


@router.post("/memberships")
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

    return success_response(
        data=MembershipResponse.model_validate(membership).model_dump(),
        message="创建会员套餐成功"
    )


@router.put("/memberships/{membership_id}")
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
        raise NotFoundException("资源不存在")

    update_data = data.model_dump()
    await db.execute(
        update(Membership)
        .where(Membership.id == membership_id)
        .values(**update_data)
    )
    await db.commit()
    await db.refresh(membership)

    return success_response(
        data=MembershipResponse.model_validate(membership).model_dump(),
        message="更新会员套餐成功"
    )


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

    return success_response(data={"deleted": result.rowcount > 0}, message="删除会员套餐成功")


# ==================== 会员订单管理 ====================

class OrderStatusUpdate(BaseModel):
    status: str  # pending | paid | cancelled | refunded


@router.get("/orders")
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

    return success_response(
        data={"items": items, "total": total},
        message="获取订单列表成功"
    )


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
        raise NotFoundException("资源不存在")

    await db.execute(
        update(MembershipOrder)
        .where(MembershipOrder.id == order_id)
        .values(status=data.status)
    )
    await db.commit()

    return success_response(data={"updated": True}, message="更新订单状态成功")
