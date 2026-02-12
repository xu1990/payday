"""
关注服务 - 关注/取关、粉丝列表、关注列表、关注流；与技术方案 3.3.2 一致
"""
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import Follow
from app.models.user import User
from app.models.post import Post


async def follow_user(db: AsyncSession, follower_id: str, following_id: str) -> bool:
    """关注用户。已关注则返回 False；不能关注自己。"""
    if follower_id == following_id:
        return False
    exists = await db.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id,
        )
    )
    if exists.scalar_one_or_none():
        return False
    db.add(Follow(follower_id=follower_id, following_id=following_id))
    u_following = (await db.execute(select(User).where(User.id == following_id))).scalar_one_or_none()
    u_follower = (await db.execute(select(User).where(User.id == follower_id))).scalar_one_or_none()
    if u_following:
        u_following.follower_count = (u_following.follower_count or 0) + 1
    if u_follower:
        u_follower.following_count = (u_follower.following_count or 0) + 1
    await db.commit()
    return True


async def unfollow_user(db: AsyncSession, follower_id: str, following_id: str) -> bool:
    """取关。不存在关系则返回 False。"""
    r = (
        await db.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
        )
    ).scalar_one_or_none()
    if not r:
        return False
    await db.delete(r)
    u_following = (await db.execute(select(User).where(User.id == following_id))).scalar_one_or_none()
    u_follower = (await db.execute(select(User).where(User.id == follower_id))).scalar_one_or_none()
    if u_following and (u_following.follower_count or 0) > 0:
        u_following.follower_count -= 1
    if u_follower and (u_follower.following_count or 0) > 0:
        u_follower.following_count -= 1
    await db.commit()
    return True


async def get_followers(
    db: AsyncSession,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[User], int]:
    """某用户的粉丝列表（User）及总数。"""
    count_q = select(func.count()).select_from(Follow).where(Follow.following_id == user_id)
    total = (await db.execute(count_q)).scalar() or 0
    q = (
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == user_id)
        .order_by(Follow.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(q)
    return list(result.scalars().unique().all()), total


async def get_following(
    db: AsyncSession,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[User], int]:
    """某用户关注的人列表（User）及总数。"""
    count_q = select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)
    total = (await db.execute(count_q)).scalar() or 0
    q = (
        select(User)
        .join(Follow, Follow.following_id == User.id)
        .where(Follow.follower_id == user_id)
        .order_by(Follow.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(q)
    return list(result.scalars().unique().all()), total


async def is_following(db: AsyncSession, follower_id: str, following_id: str) -> bool:
    r = await db.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id,
        )
    )
    return r.scalar_one_or_none() is not None


async def count_following_posts(db: AsyncSession, user_id: str) -> int:
    """关注流帖子总数。"""
    sub = select(Follow.following_id).where(Follow.follower_id == user_id)
    q = select(func.count()).select_from(Post).where(
        Post.user_id.in_(sub),
        Post.status == "normal",
        Post.risk_status == "approved",
    )
    return (await db.execute(q)).scalar() or 0


async def list_following_posts(
    db: AsyncSession,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> List[Post]:
    """关注流：当前用户关注的人发布的帖子（按时间倒序）。"""
    sub = select(Follow.following_id).where(Follow.follower_id == user_id)
    q = (
        select(Post)
        .where(
            Post.user_id.in_(sub),
            Post.status == "normal",
            Post.risk_status == "approved",
        )
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(q)
    return list(result.scalars().all())
