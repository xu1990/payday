"""
评论服务 - 按帖子分页列表、发表评论/回复、删除；管理端列表与人工审核；更新 Post.comment_count；评论/回复时创建通知
"""
from typing import List, Optional, Tuple

from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.post import Post
from app.services import notification_service
from app.core.exceptions import NotFoundException


async def list_by_post(
    db: AsyncSession,
    post_id: str,
    limit: int = 20,
    offset: int = 0,
) -> List[Comment]:
    q = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_roots_with_replies(
    db: AsyncSession,
    post_id: str,
    limit: int = 20,
    offset: int = 0,
) -> List[Comment]:
    """先查根评论分页，再批量查其回复，组装为树（每个根 comment 带 replies 列表）。"""
    roots_q = (
        select(Comment)
        .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
        .order_by(Comment.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    r = await db.execute(roots_q)
    roots = list(r.scalars().all())
    if not roots:
        return []
    root_ids = [c.id for c in roots]
    replies_q = (
        select(Comment)
        .where(Comment.post_id == post_id, Comment.parent_id.in_(root_ids))
        .order_by(Comment.created_at.asc())
    )
    r2 = await db.execute(replies_q)
    replies = list(r2.scalars().all())
    by_parent: dict[str, list[Comment]] = {}
    for c in replies:
        pid = c.parent_id or ""
        by_parent.setdefault(pid, []).append(c)
    for root in roots:
        setattr(root, "replies", by_parent.get(root.id, []))
    return roots


async def create(
    db: AsyncSession,
    post_id: str,
    user_id: str,
    anonymous_name: str,
    content: str,
    parent_id: Optional[str] = None,
) -> Comment:
    # SECURITY: 使用显式事务边界隔离所有数据库操作
    # 这样可以防止竞态条件，确保数据一致性
    from sqlalchemy import select

    comment = Comment(
        post_id=post_id,
        user_id=user_id,
        anonymous_name=anonymous_name,
        content=content,
        parent_id=parent_id,
    )

    try:
        # 开始事务
        async with db.begin():
            # 添加评论
            db.add(comment)
            await db.flush()

            # 原子性更新帖子评论数
            await db.execute(
                update(Post).where(Post.id == post_id).values(comment_count=Post.comment_count + 1)
            )

            # 通知：根评论通知帖子作者，回复通知被回复人
            r = await db.execute(select(Post).where(Post.id == post_id))
            post = r.scalar_one_or_none()
            if post and str(post.user_id) != str(user_id) and parent_id is None:
                await notification_service.create_notification(
                    db, str(post.user_id), "comment", "新评论", content or "", comment.id
                )
            if parent_id:
                parent = await get_by_id(db, parent_id)
                if parent and str(parent.user_id) != str(user_id):
                    await notification_service.create_notification(
                        db, str(parent.user_id), "reply", "新回复", content or "", comment.id
                    )

            # 提交事务
            await db.commit()

            # 刷新评论对象以获取数据库生成的值
            await db.refresh(comment)
            return comment
    except SQLAlchemyError as e:
        await db.rollback()
        raise


async def get_by_id(db: AsyncSession, comment_id: str) -> Optional[Comment]:
    r = await db.execute(select(Comment).where(Comment.id == comment_id))
    return r.scalar_one_or_none()


async def delete(db: AsyncSession, comment_id: str) -> bool:
    comment = await get_by_id(db, comment_id)
    if not comment:
        return False
    post_id = comment.post_id
    await db.delete(comment)
    await db.flush()
    # 防止 comment_count 减到负数
    r = await db.execute(select(Post).where(Post.id == post_id))
    post = r.scalar_one_or_none()
    if post:
        post.comment_count = max(0, (post.comment_count or 0) - 1)
    try:
        await db.commit()
        return True
    except SQLAlchemyError:
        await db.rollback()
        raise


async def list_comments_for_admin(
    db: AsyncSession,
    post_id: Optional[str] = None,
    risk_status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Comment], int]:
    """管理端评论列表：可选按 post_id、risk_status 筛选"""
    base = select(Comment)
    count_base = select(func.count()).select_from(Comment)
    if post_id:
        base = base.where(Comment.post_id == post_id)
        count_base = count_base.where(Comment.post_id == post_id)
    if risk_status:
        base = base.where(Comment.risk_status == risk_status)
        count_base = count_base.where(Comment.risk_status == risk_status)
    total = (await db.execute(count_base)).scalar() or 0
    q = base.order_by(Comment.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def update_comment_risk_for_admin(
    db: AsyncSession,
    comment_id: str,
    risk_status: str,
    risk_reason: Optional[str] = None,
) -> Optional[Comment]:
    """管理端人工审核评论（通过/拒绝）"""
    comment = await get_by_id(db, comment_id)
    if not comment:
        raise NotFoundException("评论不存在")
    comment.risk_status = risk_status
    # 简化逻辑：仅在字段存在且提供了新值时更新
    if risk_reason is not None and hasattr(comment, "risk_reason"):
        comment.risk_reason = risk_reason
    try:
        await db.commit()
        await db.refresh(comment)
        return comment
    except SQLAlchemyError:
        await db.rollback()
        raise
