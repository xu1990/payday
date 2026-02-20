"""
关注服务 - 关注/取关、粉丝列表、关注列表、关注流；与技术方案 3.3.2 一致
"""
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import Follow
from app.models.user import User
from app.models.post import Post
from app.services.notification_service import create_notification


async def follow_user(db: AsyncSession, follower_id: str, following_id: str) -> bool:
    """关注用户。已关注则返回 False；不能关注自己。"""
    if follower_id == following_id:
        return False

    # 先检查是否已关注
    existing = await db.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id,
        )
    )
    if existing.scalar_one_or_none():
        # 已关注，返回False表示未创建新关注
        return False

    try:
        # 直接尝试插入，依赖唯一约束防止重复
        db.add(Follow(follower_id=follower_id, following_id=following_id))
        await db.flush()

        u_following = (await db.execute(select(User).where(User.id == following_id))).scalar_one_or_none()
        u_follower = (await db.execute(select(User).where(User.id == follower_id))).scalar_one_or_none()

        if u_following:
            u_following.follower_count = (u_following.follower_count or 0) + 1
        if u_follower:
            u_follower.following_count = (u_follower.following_count or 0) + 1

        try:
            await db.commit()

            # Create notification for the user being followed
            # This happens after successful commit, but notification is in same transaction
            # If notification fails, we don't want to fail the follow operation
            try:
                if u_follower and u_following:
                    await create_notification(
                        db=db,
                        user_id=following_id,  # The user being followed
                        type="follow",
                        title="新粉丝",
                        content=f"{u_follower.anonymous_name} 关注了你",
                        related_id=follower_id,  # Store follower's user_id for reference
                    )
                    await db.commit()
            except Exception:
                # Log error but don't fail the follow operation
                # Notification failure shouldn't break the follow feature
                await db.rollback()

            return True
        except SQLAlchemyError:
            await db.rollback()
            raise
    except IntegrityError:
        # 并发情况下，唯一约束冲突说明已关注
        await db.rollback()
        return True  # 已存在，返回True表示成功（幂等）


async def unfollow_user(db: AsyncSession, follower_id: str, following_id: str) -> bool:
    """取关。不存在关系则返回 False。"""
    try:
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
        await db.flush()

        u_following = (await db.execute(select(User).where(User.id == following_id))).scalar_one_or_none()
        u_follower = (await db.execute(select(User).where(User.id == follower_id))).scalar_one_or_none()

        if u_following and (u_following.follower_count or 0) > 0:
            u_following.follower_count -= 1
        if u_follower and (u_follower.following_count or 0) > 0:
            u_follower.following_count -= 1

        try:
            await db.commit()
            return True
        except SQLAlchemyError:
            await db.rollback()
            raise
    except Exception:
        await db.rollback()
        raise


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
