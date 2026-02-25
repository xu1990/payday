"""积分退货服务 - Sprint 4.7 商品兑换系统"""
from datetime import datetime
from typing import List, Optional

from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.point_order import PointOrder
from app.models.point_return import PointReturn
from app.services.ability_points_service import add_points
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

# ============== 退货管理（用户）=============

async def create_return(
    db: AsyncSession,
    order_id: str,
    reason: str,
) -> PointReturn:
    """
    创建退货申请（用户）

    逻辑：
    1. 检查订单是否存在且属于当前用户
    2. 检查订单状态（只有pending订单可以申请退货）
    3. 创建退货申请
    """
    # 1. 查询订单
    result = await db.execute(
        select(PointOrder).where(PointOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundException("订单不存在")

    if order.status != "pending":
        raise BusinessException("只有待处理订单可以申请退货", code="ORDER_NOT_PENDING")

    # 2. 检查是否已有退货申请
    existing_return_result = await db.execute(
        select(PointReturn).where(
            and_(PointReturn.order_id == order_id,
                 PointReturn.status.in_(["requested", "approved"]))
        )
    )
    existing_return = existing_return_result.scalar_one_or_none()

    if existing_return:
        if existing_return.status == "approved":
            raise BusinessException("该订单已被批准退货，无需重复申请", code="RETURN_ALREADY_APPROVED")
        else:
            raise BusinessException("该订单已有退货申请正在处理中", code="RETURN_PENDING")

    # 3. 创建退货申请
    return_request = PointReturn(
        order_id=order_id,
        reason=reason,
        status="requested",
    )
    db.add(return_request)

    await db.commit()
    await db.refresh(return_request)
    return return_request


async def list_returns(
    db: AsyncSession,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[PointReturn]:
    """获取退货申请列表"""
    query = select(PointReturn)

    if status:
        query = query.where(PointReturn.status == status)

    query = query.order_by(PointReturn.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_return(db: AsyncSession, return_id: str) -> PointReturn:
    """获取退货申请详情"""
    result = await db.execute(
        select(PointReturn).where(PointReturn.id == return_id)
    )
    return_request = result.scalar_one_or_none()

    if not return_request:
        raise NotFoundException("退货申请不存在")

    return return_request


# ============== 退货处理（管理员）=============

async def approve_return(
    db: AsyncSession,
    return_id: str,
    admin_id: str,
    admin_notes: Optional[str] = None,
) -> PointReturn:
    """
    批准退货申请（管理员）

    逻辑：
    1. 检查退货申请状态（只有requested状态可以批准）
    2. 更新退货状态为approved
    3. 退还积分给用户
    4. 更新订单状态为cancelled
    """
    # 1. 查询退货申请
    result = await db.execute(
        select(PointReturn).where(PointReturn.id == return_id).with_for_update()
    )
    return_request = result.scalar_one_or_none()

    if not return_request:
        raise NotFoundException("退货申请不存在")

    if return_request.status != "requested":
        raise BusinessException("只能处理待审核的退货申请", code="RETURN_NOT_REQUESTED")

    # 2. 查询订单
    order_result = await db.execute(
        select(PointOrder).where(PointOrder.id == return_request.order_id)
    )
    order = order_result.scalar_one_or_none()

    if not order:
        raise NotFoundException("订单不存在")

    # 3. 更新退货申请状态
    return_request.status = "approved"
    return_request.admin_id = admin_id
    return_request.admin_notes = admin_notes
    return_request.processed_at = datetime.utcnow()

    # 4. 退还积分
    await add_points(
        db,
        order.user_id,
        order.points_cost,
        event_type="return_approved",
        reference_id=return_request.id,
        reference_type="point_return",
        description=f"退货退款: {order.product_name}"
    )

    # 5. 更新订单状态
    order.status = "cancelled"
    order.notes_admin = admin_notes

    await db.commit()
    await db.refresh(return_request)
    return return_request


async def reject_return(
    db: AsyncSession,
    return_id: str,
    admin_id: str,
    admin_notes: Optional[str] = None,
) -> PointReturn:
    """
    拒绝退货申请（管理员）

    逻辑：
    1. 检查退货申请状态（只有requested状态可以拒绝）
    2. 更新退货状态为rejected
    3. 更新订单状态保持不变
    """
    # 1. 查询退货申请
    result = await db.execute(
        select(PointReturn).where(PointReturn.id == return_id).with_for_update()
    )
    return_request = result.scalar_one_or_none()

    if not return_request:
        raise NotFoundException("退货申请不存在")

    if return_request.status != "requested":
        raise BusinessException("只能处理待审核的退货申请", code="RETURN_NOT_REQUESTED")

    # 2. 更新退货申请状态
    return_request.status = "rejected"
    return_request.admin_id = admin_id
    return_request.admin_notes = admin_notes
    return_request.processed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(return_request)
    return return_request