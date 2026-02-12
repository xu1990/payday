"""
会员服务 - Sprint 3.5 会员订单、权益验证
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership, MembershipOrder, User
from app.schemas.membership import MembershipOrderCreate


async def list_memberships(db: AsyncSession) -> List[Membership]:
    """获取所有可用会员套餐"""
    result = await db.execute(
        select(Membership)
        .where(Membership.is_active == True)
        .order_by(Membership.sort_order, Membership.price)
    )
    return list(result.scalars().all())


async def create_order(
    db: AsyncSession,
    user_id: str,
    membership_id: str,
    amount: float,
    payment_method: str = "wechat",
    transaction_id: Optional[str] = None,
) -> MembershipOrder:
    """创建会员订单"""
    # 获取套餐信息
    membership = await db.execute(
        select(Membership).where(Membership.id == membership_id)
    )
    membership_obj = membership.scalar_one_or_none()
    if not membership_obj:
        raise ValueError("Invalid membership ID")
    if not membership_obj.is_active:
        raise ValueError("Membership is not active")

    # 计算会员起止日期
    start_date = datetime.utcnow().date()
    end_date = start_date + timedelta(days=membership_obj.duration_days)

    order = MembershipOrder(
        user_id=user_id,
        membership_id=membership_id,
        amount=amount,
        status="pending",
        payment_method=payment_method,
        transaction_id=transaction_id,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def get_my_orders(db: AsyncSession, user_id: str) -> List[MembershipOrder]:
    """获取我的会员订单"""
    result = await db.execute(
        select(MembershipOrder)
        .where(MembershipOrder.user_id == user_id)
        .order_by(MembershipOrder.created_at.desc())
    )
    return list(result.scalars().all())


async def get_active_membership(db: AsyncSession, user_id: str) -> Optional[dict]:
    """获取用户当前激活的会员（如果有）"""
    # 查找最新的有效订单
    result = await db.execute(
        select(MembershipOrder)
        .where(
            and_(
                MembershipOrder.user_id == user_id,
                MembershipOrder.status == "paid",
            ),
            MembershipOrder.end_date >= datetime.utcnow().date(),
        )
        .order_by(MembershipOrder.created_at.desc())
    )
    active_order = result.scalar_one_or_none()

    if not active_order:
        return None

    membership = await db.execute(
        select(Membership).where(Membership.id == active_order.membership_id)
    ).scalar_one_or_none()

    if not membership:
        return None

    return {
        "id": membership.id,
        "name": membership.name,
        "description": membership.description,
        "end_date": active_order.end_date.isoformat(),
        "days_remaining": (active_order.end_date.date() - datetime.utcnow().date()).days + 1,
    }


async def verify_membership_benefits(db: AsyncSession, user_id: str, endpoint: str) -> bool:
    """验证用户是否有权限访问特定功能（会员权益验证）"""
    active = await get_active_membership(db, user_id)
    if not active:
        return False

    # 根据端点判断所需会员等级
    # 这里简化处理：所有会员功能都验证
    return True


async def cancel_order(db: AsyncSession, order_id: str, user_id: str) -> bool:
    """取消会员订单

    只能取消状态为 pending 的订单
    """
    from sqlalchemy import update

    # 查询订单
    result = await db.execute(
        select(MembershipOrder)
        .where(
            and_(
                MembershipOrder.id == order_id,
                MembershipOrder.user_id == user_id,
            )
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise ValueError("订单不存在")

    if order.status != "pending":
        raise ValueError(f"订单状态为 {order.status}，无法取消")

    # 更新订单状态
    await db.execute(
        update(MembershipOrder)
        .where(MembershipOrder.id == order_id)
        .values(status="cancelled")
    )
    await db.commit()
    return True
