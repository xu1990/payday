"""Savings Goal API - 存款目标接口（Sprint 4.4）"""
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import success_response
from app.models.user import User
from app.schemas.savings_goal import (SavingsGoalCreate, SavingsGoalDeposit, SavingsGoalResponse,
                                      SavingsGoalUpdate)
from app.services.savings_goal_service import (add_deposit, create_savings_goal,
                                               delete_savings_goal, get_savings_goal_by_id,
                                               goal_to_response, list_savings_goals,
                                               update_savings_goal)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/savings-goals", tags=["savings-goals"])


@router.post("")
async def create_goal(
    body: SavingsGoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建存款目标"""
    goal = await create_savings_goal(db, current_user.id, body)
    response = SavingsGoalResponse(**goal_to_response(goal))
    return success_response(data=response.model_dump(mode='json'), message="存款目标创建成功")


@router.get("")
async def get_goals(
    status: str = Query(None, description="筛选状态"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的存款目标列表"""
    goals = await list_savings_goals(db, current_user.id, status)
    response = [SavingsGoalResponse(**goal_to_response(g)).model_dump(mode='json') for g in goals]
    return success_response(data={"goals": response, "total": len(response)})


@router.get("/{goal_id}")
async def get_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个存款目标详情"""
    goal = await get_savings_goal_by_id(db, goal_id, current_user.id)
    if not goal:
        return success_response(data=None, message="目标不存在", code="NOT_FOUND")
    response = SavingsGoalResponse(**goal_to_response(goal))
    return success_response(data=response.model_dump(mode='json'))


@router.put("/{goal_id}")
async def update_goal(
    goal_id: str,
    body: SavingsGoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新存款目标"""
    goal = await update_savings_goal(db, goal_id, current_user.id, body)
    response = SavingsGoalResponse(**goal_to_response(goal))
    return success_response(data=response.model_dump(mode='json'), message="存款目标更新成功")


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除存款目标（软删除）"""
    success = await delete_savings_goal(db, goal_id, current_user.id)
    if not success:
        return success_response(data=None, message="目标不存在", code="NOT_FOUND")
    return success_response(data={"deleted": True}, message="存款目标已删除")


@router.post("/{goal_id}/deposit")
async def deposit_to_goal(
    goal_id: str,
    body: SavingsGoalDeposit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """向目标存入金额"""
    goal = await add_deposit(db, goal_id, current_user.id, body.amount)
    response = SavingsGoalResponse(**goal_to_response(goal))
    return success_response(data=response.model_dump(mode='json'), message="存款成功")
