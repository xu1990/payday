"""Savings Goal Service - 存款目标服务（Sprint 4.4）"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from app.models.savings_goal import SavingsGoal
from app.schemas.savings_goal import SavingsGoalCreate, SavingsGoalUpdate
from app.core.exceptions import NotFoundException, ValidationException


async def create_savings_goal(
    db: AsyncSession,
    user_id: str,
    data: SavingsGoalCreate
) -> SavingsGoal:
    """创建存款目标"""
    from app.services.ability_points_service import trigger_event

    goal = SavingsGoal(
        user_id=user_id,
        title=data.title,
        description=data.description,
        target_amount=data.target_amount,
        current_amount=data.current_amount,
        deadline=data.deadline,
        start_date=data.start_date or date.today(),
        category=data.category,
        icon=data.icon,
        status="active",
    )

    # 如果当前金额已达到目标，标记为完成
    was_completed = goal.current_amount >= goal.target_amount
    if was_completed:
        goal.status = "completed"
        goal.completed_at = datetime.utcnow()

    db.add(goal)
    await db.commit()
    await db.refresh(goal)

    # 发放积分
    if was_completed:
        # 如果创建时就已完成，只发完成积分
        await trigger_event(
            db, user_id, "savings_goal_complete",
            reference_id=str(goal.id),
            reference_type="savings_goal",
            description="完成存款目标"
        )
    else:
        # 创建积分
        await trigger_event(
            db, user_id, "savings_goal_create",
            reference_id=str(goal.id),
            reference_type="savings_goal",
            description="创建存款目标"
        )

    return goal


async def get_savings_goal_by_id(
    db: AsyncSession,
    goal_id: str,
    user_id: str
) -> Optional[SavingsGoal]:
    """获取用户的存款目标"""
    result = await db.execute(
        select(SavingsGoal).where(
            SavingsGoal.id == goal_id,
            SavingsGoal.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def list_savings_goals(
    db: AsyncSession,
    user_id: str,
    status: Optional[str] = None
) -> List[SavingsGoal]:
    """获取用户的存款目标列表"""
    query = select(SavingsGoal).where(SavingsGoal.user_id == user_id)

    if status:
        query = query.where(SavingsGoal.status == status)

    query = query.order_by(SavingsGoal.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_savings_goal(
    db: AsyncSession,
    goal_id: str,
    user_id: str,
    data: SavingsGoalUpdate
) -> Optional[SavingsGoal]:
    """更新存款目标"""
    from app.services.ability_points_service import trigger_event

    goal = await get_savings_goal_by_id(db, goal_id, user_id)
    if not goal:
        raise NotFoundException("存款目标不存在")

    # 记录之前的状态
    was_completed_before = goal.status == "completed"

    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)

    # 检查是否完成
    just_completed = False
    if goal.current_amount >= goal.target_amount and goal.status != "completed":
        goal.status = "completed"
        goal.completed_at = datetime.utcnow()
        just_completed = True

    await db.commit()
    await db.refresh(goal)

    # 如果刚刚完成，发放完成积分（之前未完成，现在完成了）
    if just_completed and not was_completed_before:
        await trigger_event(
            db, user_id, "savings_goal_complete",
            reference_id=str(goal.id),
            reference_type="savings_goal",
            description="完成存款目标"
        )

    return goal


async def delete_savings_goal(
    db: AsyncSession,
    goal_id: str,
    user_id: str
) -> bool:
    """删除存款目标（软删除，设置为cancelled状态）"""
    goal = await get_savings_goal_by_id(db, goal_id, user_id)
    if not goal:
        return False

    goal.status = "cancelled"
    await db.commit()
    return True


async def add_deposit(
    db: AsyncSession,
    goal_id: str,
    user_id: str,
    amount: float
) -> Optional[SavingsGoal]:
    """向目标存入金额"""
    from app.services.ability_points_service import trigger_event

    # 验证金额合理性
    if amount <= 0:
        raise ValidationException("存款金额必须大于0")
    if amount > 1000000:  # 防止异常大额存款
        raise ValidationException("存款金额超出合理范围")

    goal = await get_savings_goal_by_id(db, goal_id, user_id)
    if not goal:
        raise NotFoundException("存款目标不存在")

    if goal.status not in ["active", "paused"]:
        raise ValidationException("只能向活跃或暂停的目标存款")

    # 记录之前的状态
    was_completed_before = goal.status == "completed"

    # 将 float 转换为 Decimal 以匹配数据库类型
    goal.current_amount += Decimal(str(amount))

    # 检查是否完成
    just_completed = False
    if goal.current_amount >= goal.target_amount and goal.status != "completed":
        goal.status = "completed"
        goal.completed_at = datetime.utcnow()
        just_completed = True

    await db.commit()
    await db.refresh(goal)

    # 如果刚刚完成，发放完成积分（之前未完成，现在完成了）
    if just_completed and not was_completed_before:
        await trigger_event(
            db, user_id, "savings_goal_complete",
            reference_id=str(goal.id),
            reference_type="savings_goal",
            description="完成存款目标"
        )

    return goal


def goal_to_response(goal: SavingsGoal) -> dict:
    """将目标转换为响应格式"""
    progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    remaining = max(0, goal.target_amount - goal.current_amount)

    return {
        "id": goal.id,
        "user_id": goal.user_id,
        "title": goal.title,
        "description": goal.description,
        "target_amount": float(goal.target_amount),
        "current_amount": float(goal.current_amount),
        "deadline": goal.deadline,
        "start_date": goal.start_date,
        "status": goal.status,
        "category": goal.category,
        "icon": goal.icon,
        "progress_percentage": round(progress, 2),
        "remaining_amount": round(remaining, 2),
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "completed_at": goal.completed_at,
    }
