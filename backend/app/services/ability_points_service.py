"""Ability Points Service - 能力值系统服务（Sprint 4.6）"""
import json
from datetime import datetime
from typing import List, Optional

from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.ability_points import AbilityPoint, AbilityPointTransaction, PointRedemption
from app.schemas.ability_points import PointRedemptionCreate, PointRedemptionUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ============== 常量配置 ==============
# 积分系统常量，避免魔法数字
POINTS_PER_LEVEL = 1000  # 每升1级所需的积分


async def get_or_create_user_points(db: AsyncSession, user_id: str) -> AbilityPoint:
    """获取或创建用户积分账户（带并发处理）"""
    from sqlalchemy.exc import IntegrityError

    # 尝试获取现有积分账户
    result = await db.execute(
        select(AbilityPoint).where(AbilityPoint.user_id == user_id)
    )
    points = result.scalar_one_or_none()

    if not points:
        try:
            # 使用行级锁防止并发创建
            await db.execute(
                select(AbilityPoint)
                .where(AbilityPoint.user_id == user_id)
                .with_for_update()
            )
            points = AbilityPoint(
                user_id=user_id,
                total_points=0,
                available_points=0,
                level=1,
                total_earned=0,
                total_spent=0,
            )
            db.add(points)
            await db.commit()
            await db.refresh(points)
        except IntegrityError:
            # 并发情况下，其他事务可能已经创建了该用户积分账户
            await db.rollback()
            result = await db.execute(
                select(AbilityPoint).where(AbilityPoint.user_id == user_id)
            )
            points = result.scalar_one_or_none()

    return points


async def add_points(
    db: AsyncSession,
    user_id: str,
    amount: int,
    event_type: str,
    reference_id: Optional[str] = None,
    reference_type: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> AbilityPoint:
    """增加积分（hooks系统核心）"""
    if amount <= 0:
        raise ValidationException("积分数量必须大于0")

    # 验证 reference_id 和 reference_type 的组合合法性
    if reference_id or reference_type:
        if not reference_id or not reference_type:
            raise ValidationException("reference_id 和 reference_type 必须同时提供或同时为空")

    points = await get_or_create_user_points(db, user_id)

    # 更新积分
    points.total_points += amount
    points.available_points += amount
    points.total_earned += amount

    # 计算等级（每POINTS_PER_LEVEL分升1级）
    points.level = 1 + points.total_points // POINTS_PER_LEVEL

    # 创建交易记录
    transaction = AbilityPointTransaction(
        user_id=user_id,
        amount=amount,
        balance_after=points.available_points,
        transaction_type="earn",
        event_type=event_type,
        reference_id=reference_id,
        reference_type=reference_type,
        description=description,
        extra_metadata=json.dumps(metadata) if metadata else None,
    )
    db.add(transaction)

    await db.commit()
    await db.refresh(points)
    return points


async def spend_points(
    db: AsyncSession,
    user_id: str,
    amount: int,
    reference_id: Optional[str] = None,
    reference_type: Optional[str] = None,
    description: Optional[str] = None,
) -> AbilityPoint:
    """消费积分（带行级锁防止竞态条件）"""
    if amount <= 0:
        raise ValidationException("积分数量必须大于0")

    # 验证 reference_id 和 reference_type 的组合合法性
    if reference_id or reference_type:
        if not reference_id or not reference_type:
            raise ValidationException("reference_id 和 reference_type 必须同时提供或同时为空")

    # 使用行级锁防止并发导致的双花问题
    result = await db.execute(
        select(AbilityPoint)
        .where(AbilityPoint.user_id == user_id)
        .with_for_update()  # 行级锁
    )
    points = result.scalar_one_or_none()

    if not points:
        raise BusinessException("积分账户不存在", code="POINTS_ACCOUNT_NOT_FOUND")

    if points.available_points < amount:
        raise BusinessException("积分不足", code="INSUFFICIENT_POINTS")

    # 更新积分
    points.available_points -= amount
    points.total_spent += amount

    # 创建交易记录
    transaction = AbilityPointTransaction(
        user_id=user_id,
        amount=-amount,
        balance_after=points.available_points,
        transaction_type="spend",
        reference_id=reference_id,
        reference_type=reference_type,
        description=description,
    )
    db.add(transaction)

    await db.commit()
    await db.refresh(points)
    return points


async def get_user_transactions(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[AbilityPointTransaction]:
    """获取用户积分流水"""
    result = await db.execute(
        select(AbilityPointTransaction)
        .where(AbilityPointTransaction.user_id == user_id)
        .order_by(AbilityPointTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def create_redemption(
    db: AsyncSession,
    user_id: str,
    data: PointRedemptionCreate,
) -> PointRedemption:
    """创建积分兑换"""
    points = await get_or_create_user_points(db, user_id)

    if points.available_points < data.points_cost:
        raise BusinessException("积分不足", code="INSUFFICIENT_POINTS")

    # 扣除积分
    await spend_points(
        db, user_id, data.points_cost,
        reference_type="redemption",
        description=f"兑换: {data.reward_name}"
    )

    # 创建兑换记录
    redemption = PointRedemption(
        user_id=user_id,
        reward_name=data.reward_name,
        reward_type=data.reward_type,
        points_cost=data.points_cost,
        delivery_info=data.delivery_info,
        notes=data.notes,
        status="pending",
    )
    db.add(redemption)
    await db.commit()
    await db.refresh(redemption)
    return redemption


async def get_user_redemptions(
    db: AsyncSession,
    user_id: str,
    status: Optional[str] = None,
) -> List[PointRedemption]:
    """获取用户兑换记录"""
    query = select(PointRedemption).where(PointRedemption.user_id == user_id)

    if status:
        query = query.where(PointRedemption.status == status)

    query = query.order_by(PointRedemption.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_all_redemptions(
    db: AsyncSession,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[PointRedemption]:
    """获取所有兑换记录（管理员）"""
    query = select(PointRedemption)

    if status:
        query = query.where(PointRedemption.status == status)

    query = query.order_by(PointRedemption.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_redemption_status(
    db: AsyncSession,
    redemption_id: str,
    admin_id: str,
    data: PointRedemptionUpdate,
) -> Optional[PointRedemption]:
    """更新兑换状态（管理员）"""
    result = await db.execute(
        select(PointRedemption).where(PointRedemption.id == redemption_id)
    )
    redemption = result.scalar_one_or_none()

    if not redemption:
        raise NotFoundException("兑换记录不存在")

    if redemption.status != "pending":
        raise ValidationException("只能处理待审核的兑换")

    redemption.status = data.status
    redemption.admin_id = admin_id
    redemption.processed_at = datetime.utcnow()

    if data.status == "rejected" and data.rejection_reason:
        redemption.rejection_reason = data.rejection_reason

    # 如果拒绝，退还积分
    if data.status == "rejected":
        await add_points(
            db, redemption.user_id, redemption.points_cost,
            event_type="redemption_refund",
            reference_id=redemption_id,
            reference_type="redemption",
            description=f"兑换被拒绝，退还积分: {redemption.reward_name}"
        )

    await db.commit()
    await db.refresh(redemption)
    return redemption


# ============== Hooks系统预定义事件 ==============
# 事件类型及对应积分
POINT_EVENTS = {
    "checkin_daily": 5,          # 每日打卡
    "checkin_weekly": 20,        # 每周打卡
    "checkin_milestone": 50,     # 里程碑打卡
    "checkin_special": 100,      # 特殊打卡
    "post_create": 10,           # 发帖
    "post_liked": 2,             # 帖子被赞
    "comment_create": 3,         # 评论
    "follow_someone": 5,         # 关注他人
    "salary_record": 20,         # 记录工资
    "first_salary": 50,          # 第一笔工资
    "savings_goal_create": 10,   # 创建存款目标
    "savings_goal_complete": 100,# 完成存款目标
    # Sprint 4.7 邀请系统
    "invite_success": 30,        # 邀请用户成功
    "invited_by_someone": 10,    # 被邀请注册
    # Sprint 4.7 商品订单系统
    "order_cancelled": 0,        # 订单取消退款（动态金额）
    "order_cancelled_by_admin": 0,  # 管理员取消订单退款（动态金额）
}


async def trigger_event(
    db: AsyncSession,
    user_id: str,
    event_type: str,
    reference_id: Optional[str] = None,
    reference_type: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[AbilityPoint]:
    """触发积分事件（hooks系统入口）"""
    points = POINT_EVENTS.get(event_type)
    if not points or points <= 0:
        return None

    return await add_points(
        db, user_id, points,
        event_type=event_type,
        reference_id=reference_id,
        reference_type=reference_type,
        description=description or f"{event_type}: +{points}积分",
    )
