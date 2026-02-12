"""
用户服务 - 查询、更新用户；管理端分页列表
"""
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserUpdate


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user_id: str, data: UserUpdate) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    update_dict = data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user


async def list_users_for_admin(
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[List[User], int]:
    """管理端：用户列表分页与总数；可选按匿名昵称关键词、状态筛选"""
    base = select(User)
    count_base = select(func.count()).select_from(User)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        base = base.where(User.anonymous_name.ilike(k))
        count_base = count_base.where(User.anonymous_name.ilike(k))
    if status and status.strip():
        base = base.where(User.status == status.strip())
        count_base = count_base.where(User.status == status.strip())
    total_result = await db.execute(count_base)
    total_count = total_result.scalar() or 0
    q = base.order_by(User.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all()), total_count
