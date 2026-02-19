"""
用户服务 - 查询、更新用户；管理端分页列表
"""
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.exceptions import NotFoundException


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user_id: str, data: UserUpdate) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    update_dict = data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_profile_data(db: AsyncSession, user_id: str, target_user_id: str) -> dict:
    """获取用户主页数据 - 优化N+1查询"""
    import asyncio
    from app.models.post import Post
    from app.models.checkin import CheckIn
    from app.models.salary import SalaryRecord
    from app.models.follow import Follow
    from sqlalchemy import func

    # 并发查询所有数据
    posts_task = db.execute(
        select(Post)
        .where(
            Post.user_id == target_user_id,
            Post.status == "normal",
            Post.risk_status == "approved"
        )
        .order_by(Post.created_at.desc())
        .limit(20)
    )

    checkins_task = db.execute(
        select(CheckIn)
        .where(CheckIn.user_id == target_user_id)
        .order_by(CheckIn.check_date.desc())
        .limit(30)
    )

    follower_count_task = db.execute(
        select(func.count(Follow.id))
        .select_from(Follow)
        .where(Follow.following_id == target_user_id)
    )

    following_count_task = db.execute(
        select(func.count(Follow.id))
        .select_from(Follow)
        .where(Follow.follower_id == target_user_id)
    )

    # 并发执行所有查询
    posts_result, checkins_result, follower_count_result, following_count_result = await asyncio.gather(
        posts_task, checkins_task, follower_count_task, following_count_task
    )

    posts = posts_result.scalars().all()
    checkins = checkins_result.scalars().all()
    follower_count = follower_count_result.scalar() or 0
    following_count = following_count_result.scalar() or 0

    return {
        "posts": [p.id for p in posts],
        "checkins": [c.id for c in checkins],
        "follower_count": follower_count,
        "following_count": following_count
    }


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


async def deactivate_user(db: AsyncSession, user_id: str) -> User:
    """注销用户（软删除）"""
    from datetime import datetime, timedelta
    from sqlalchemy import update, select

    # 设置注销时间
    result = await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(deactivated_at=datetime.utcnow())
        .returning(User)
    )
    await db.commit()

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    return user


async def reactivate_user(db: AsyncSession, user_id: str) -> User:
    """恢复已注销的用户"""
    from sqlalchemy import update, select

    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(deactivated_at=None)
    )
    await db.commit()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    return user


async def upload_user_avatar(db: AsyncSession, user_id: str, avatar_url: str) -> User:
    """更新用户头像"""
    return await update_user(db, user_id, UserUpdate(avatar=avatar_url))
