"""邀请服务 - Sprint 4.7 邀请系统"""
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_invitation import UserInvitation
from app.models.ability_points import AbilityPointTransaction
from app.utils.invite_code import get_or_create_invite_code, validate_invite_code
from app.services.ability_points_service import add_points
from app.core.exceptions import BusinessException, ValidationException

# 常量配置
INVITER_REWARD_POINTS = 30  # 邀请者奖励积分
INVITEE_REWARD_POINTS = 10  # 被邀请者奖励积分


async def get_my_invite_code(db: AsyncSession, user_id: str) -> str:
    """获取我的邀请码（如果不存在则自动生成）"""
    return await get_or_create_invite_code(db, user_id)


async def get_invitation_stats(db: AsyncSession, user_id: str) -> dict:
    """
    获取邀请统计信息

    Returns:
        {
            "invite_code": "ABCD1234",
            "total_invited": 10,
            "total_points_earned": 300
        }
    """
    # 获取邀请码
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise BusinessException("用户不存在", code="USER_NOT_FOUND")

    # 统计邀请人数
    invite_result = await db.execute(
        select(UserInvitation).where(UserInvitation.inviter_id == user_id)
    )
    invitations = list(invite_result.scalars().all())

    # 计算获得积分（仅计算已发放的）
    total_points = len(invitations) * INVITER_REWARD_POINTS

    return {
        "invite_code": user.invite_code or "",
        "total_invited": len(invitations),
        "total_points_earned": total_points,
    }


async def process_invitation(
    db: AsyncSession,
    inviter: User,
    invitee: User,
    invite_code: str
) -> Tuple[Optional[AbilityPointTransaction], Optional[AbilityPointTransaction]]:
    """
    处理邀请奖励（内部函数）

    Args:
        db: 数据库会话
        inviter: 邀请者用户对象
        invitee: 被邀请者用户对象
        invite_code: 使用的邀请码

    Returns:
        (邀请者积分流水, 被邀请者积分流水)

    Raises:
        BusinessException: 业务逻辑错误
    """
    # 1. 给邀请者加积分
    inviter_transaction = await add_points(
        db,
        inviter.id,
        INVITER_REWARD_POINTS,
        event_type="invite_success",
        reference_id=invitee.id,
        reference_type="user_invitation",
        description=f"邀请用户注册成功 +{INVITER_REWARD_POINTS}积分"
    )

    # 2. 给被邀请者加积分
    invitee_transaction = await add_points(
        db,
        invitee.id,
        INVITEE_REWARD_POINTS,
        event_type="invited_by_someone",
        reference_id=inviter.id,
        reference_type="user_invitation",
        description=f"使用邀请码注册 +{INVITEE_REWARD_POINTS}积分"
    )

    # 3. 创建邀请关系记录
    invitation = UserInvitation(
        inviter_id=inviter.id,
        invitee_id=invitee.id,
        invite_code_used=invite_code,
        inviter_points_rewarded=inviter_transaction.id,
        invitee_points_rewarded=invitee_transaction.id,
    )
    db.add(invitation)

    await db.commit()
    await db.refresh(invitation)

    return inviter_transaction, invitee_transaction


async def apply_invite_code(
    db: AsyncSession,
    user_id: str,
    invite_code: str
) -> dict:
    """
    应用邀请码（用户注册时调用）

    Args:
        db: 数据库会话
        user_id: 当前用户ID
        invite_code: 邀请码

    Returns:
        {
            "success": true,
            "inviter_id": "...",
            "points_earned": 10
        }

    Raises:
        ValidationException: 参数错误
        BusinessException: 业务逻辑错误
    """
    # 1. 基础验证
    if not invite_code:
        raise ValidationException("邀请码不能为空", details={"invite_code": "不能为空"})

    # 2. 查询当前用户
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise BusinessException("用户不存在", code="USER_NOT_FOUND")

    # 3. 检查是否已经被邀请过
    if user.invited_by:
        raise BusinessException("您已经使用过邀请码", code="ALREADY_INVITED")

    # 4. 验证邀请码并获取邀请者
    inviter = await validate_invite_code(db, invite_code)
    if not inviter:
        raise ValidationException("邀请码无效", details={"invite_code": "无效的邀请码"})

    # 5. 防止自己邀请自己
    if inviter.id == user.id:
        raise ValidationException("不能使用自己的邀请码", details={"invite_code": "不能使用自己的邀请码"})

    # 6. 检查是否已经邀请过该用户（通过user_invitations表）
    existing_invitation = await db.execute(
        select(UserInvitation).where(UserInvitation.invitee_id == user.id)
    )
    if existing_invitation.scalar_one_or_none():
        raise BusinessException("您已经使用过邀请码", code="ALREADY_INVITED")

    # 7. 处理邀请奖励
    inviter_tx, invitee_tx = await process_invitation(db, inviter, user, invite_code)

    # 8. 更新用户的invited_by字段
    user.invited_by = inviter.id
    await db.commit()

    return {
        "success": True,
        "inviter_id": inviter.id,
        "points_earned": INVITEE_REWARD_POINTS,
    }


async def get_my_invitations(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> list:
    """
    获取我邀请的用户列表

    Returns:
        [{
            "invitee_id": "...",
            "invitee_name": "打工人1234",
            "created_at": "2026-02-23T10:00:00",
            "points_rewarded": 30
        }]
    """
    # 查询邀请记录
    result = await db.execute(
        select(UserInvitation)
        .where(UserInvitation.inviter_id == user_id)
        .order_by(UserInvitation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    invitations = list(result.scalars().all())

    # 获取被邀请者信息
    invitee_ids = [inv.invitee_id for inv in invitations]
    if not invitee_ids:
        return []

    users_result = await db.execute(
        select(User).where(User.id.in_(invitee_ids))
    )
    users = {u.id: u for u in users_result.scalars().all()}

    # 组装数据
    data = []
    for inv in invitations:
        invitee = users.get(inv.invitee_id)
        if invitee:
            data.append({
                "invitee_id": invitee.id,
                "invitee_name": invitee.anonymous_name,
                "created_at": inv.created_at.isoformat(),
                "points_rewarded": INVITER_REWARD_POINTS if inv.inviter_points_rewarded else 0,
            })

    return data
