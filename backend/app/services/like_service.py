"""
点赞服务 - 帖子/评论点赞与取消，维护 Post.like_count / Comment.like_count；点赞时创建通知
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.services import notification_service
from app.core.cache import LikeCacheService


async def _get_like(
    db: AsyncSession, user_id: str, target_type: str, target_id: str
):
    r = await db.execute(
        select(Like).where(
            Like.user_id == user_id,
            Like.target_type == target_type,
            Like.target_id == target_id,
        )
    )
    return r.scalar_one_or_none()


async def like_post(db: AsyncSession, user_id: str, post_id: str) -> tuple["Like | None", bool]:
    """对帖子点赞；已赞则幂等返回。返回 (like, created)。"""
    try:
        like = Like(user_id=user_id, target_type="post", target_id=post_id)
        db.add(like)
        await db.flush()

        r = await db.execute(select(Post).where(Post.id == post_id))
        post = r.scalar_one_or_none()
        if post:
            post.like_count = (post.like_count or 0) + 1
            if str(post.user_id) != str(user_id):
                await notification_service.create_notification(
                    db, str(post.user_id), "like", "新点赞", "", post_id
                )

        try:
            await db.commit()
            await db.refresh(like)
        except SQLAlchemyError:
            await db.rollback()
            raise

        # 更新缓存
        try:
            LikeCacheService.set_like_status(user_id, "post", post_id)
        except Exception as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to set like status for post {post_id}: {e}")
        return like, True
    except IntegrityError:
        # 并发情况下，唯一约束冲突说明已存在
        await db.rollback()
        existing = await _get_like(db, user_id, "post", post_id)
        return existing, False


async def unlike_post(db: AsyncSession, user_id: str, post_id: str) -> bool:
    """取消帖子点赞。"""
    try:
        like = await _get_like(db, user_id, "post", post_id)
        if not like:
            return False

        await db.delete(like)
        await db.flush()

        r = await db.execute(select(Post).where(Post.id == post_id))
        post = r.scalar_one_or_none()
        if post:
            post.like_count = max(0, (post.like_count or 0) - 1)

        try:
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise

        # 移除缓存
        try:
            LikeCacheService.remove_like_status(user_id, "post", post_id)
        except Exception as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to remove like status for post {post_id}: {e}")
        return True
    except Exception:
        await db.rollback()
        raise


async def like_comment(db: AsyncSession, user_id: str, comment_id: str) -> tuple["Like | None", bool]:
    """对评论点赞；已赞则幂等返回。返回 (like, created)。"""
    try:
        like = Like(user_id=user_id, target_type="comment", target_id=comment_id)
        db.add(like)
        await db.flush()

        r = await db.execute(select(Comment).where(Comment.id == comment_id))
        comment = r.scalar_one_or_none()
        if comment:
            comment.like_count = (comment.like_count or 0) + 1
            if str(comment.user_id) != str(user_id):
                await notification_service.create_notification(
                    db, str(comment.user_id), "like", "新点赞", "", comment_id
                )

        try:
            await db.commit()
            await db.refresh(like)
        except SQLAlchemyError:
            await db.rollback()
            raise

        # 更新缓存
        try:
            LikeCacheService.set_like_status(user_id, "comment", comment_id)
        except Exception as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to set like status for comment {comment_id}: {e}")
        return like, True
    except IntegrityError:
        # 并发情况下，唯一约束冲突说明已存在
        await db.rollback()
        existing = await _get_like(db, user_id, "comment", comment_id)
        return existing, False


async def unlike_comment(db: AsyncSession, user_id: str, comment_id: str) -> bool:
    """取消评论点赞。"""
    try:
        like = await _get_like(db, user_id, "comment", comment_id)
        if not like:
            return False

        await db.delete(like)
        await db.flush()

        r = await db.execute(select(Comment).where(Comment.id == comment_id))
        comment = r.scalar_one_or_none()
        if comment:
            comment.like_count = max(0, (comment.like_count or 0) - 1)

        try:
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise

        # 移除缓存
        try:
            LikeCacheService.remove_like_status(user_id, "comment", comment_id)
        except Exception as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to remove like status for comment {comment_id}: {e}")
        return True
    except Exception:
        await db.rollback()
        raise


async def is_liked(
    db: AsyncSession, user_id: str, target_type: str, target_id: str
) -> bool:
    """检查是否已点赞，先查缓存，缓存未命中则查数据库"""
    # 先检查缓存
    try:
        if LikeCacheService.is_liked(user_id, target_type, target_id):
            return True
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"Failed to check like status in cache: {e}")
    # 缓存未命中，查数据库
    like = await _get_like(db, user_id, target_type, target_id)
    return like is not None
