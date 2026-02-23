"""邀请码生成工具"""
import random
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.exceptions import BusinessException


def generate_invite_code() -> str:
    """
    生成8位唯一邀请码

    规则：
    - 长度8位
    - 字符集：数字(0-9) + 大写字母（去除O, I等易混淆字符）
    - 确保唯一性（由调用方检查）

    示例：A3B7K9M2, P4Q8R2T1
    """
    # 去除易混淆字符：O, I
    chars = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return ''.join(random.choices(chars, k=8))


async def get_or_create_invite_code(db: AsyncSession, user_id: str) -> str:
    """
    获取或创建用户邀请码

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        邀请码

    Raises:
        BusinessException: 用户不存在
    """
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise BusinessException("用户不存在", code="USER_NOT_FOUND")

    # 如果已有邀请码，直接返回
    if user.invite_code:
        return user.invite_code

    # 生成新的邀请码（带重试机制）
    max_attempts = 10
    for _ in range(max_attempts):
        code = generate_invite_code()

        # 检查是否已存在
        existing = await db.execute(
            select(User).where(User.invite_code == code)
        )
        if existing.scalar_one_or_none() is None:
            # 找到可用的邀请码
            user.invite_code = code
            await db.commit()
            await db.refresh(user)
            return code

    # 如果10次都没找到可用的（极低概率），抛出异常
    raise BusinessException("生成邀请码失败，请重试", code="INVITE_CODE_GENERATION_FAILED")


async def validate_invite_code(db: AsyncSession, code: str) -> Optional[User]:
    """
    验证邀请码是否有效

    Args:
        db: 数据库会话
        code: 邀请码

    Returns:
        邀请者用户对象，如果无效返回None
    """
    if not code or len(code) != 8:
        return None

    result = await db.execute(
        select(User).where(User.invite_code == code)
    )
    return result.scalar_one_or_none()
