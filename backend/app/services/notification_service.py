"""
通知服务 - 列表、未读数、标记已读、创建通知（供评论/点赞调用）
"""
from __future__ import annotations

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    user_id: str,
    type: str,
    title: str,
    content: str | None = None,
    related_id: str | None = None,
) -> Notification:
    """创建一条通知（接收者 user_id）。"""
    n = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        related_id=related_id,
    )
    db.add(n)
    await db.flush()
    await db.refresh(n)
    return n


async def list_notifications(
    db: AsyncSession,
    user_id: str,
    unread_only: bool = False,
    type_filter: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Notification], int]:
    """当前用户的通知列表与总数。"""
    q = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        q = q.where(Notification.is_read == False)
    if type_filter:
        q = q.where(Notification.type == type_filter)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
    r = await db.execute(q)
    return list(r.scalars().all()), total


async def get_unread_count(db: AsyncSession, user_id: str) -> int:
    """当前用户未读通知数量。"""
    q = (
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
    )
    r = await db.execute(q)
    return r.scalar() or 0


async def mark_read(
    db: AsyncSession,
    user_id: str,
    notification_ids: list[str],
) -> int:
    """将指定 id 的通知标记为已读（仅限当前用户）。返回更新条数。"""
    if not notification_ids:
        return 0
    r = await db.execute(
        update(Notification)
        .where(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id,
        )
        .values(is_read=True)
    )
    await db.commit()
    return r.rowcount


async def mark_all_read(db: AsyncSession, user_id: str) -> int:
    """将当前用户全部通知标记为已读。返回更新条数。"""
    r = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return r.rowcount


async def mark_one_read(
    db: AsyncSession,
    user_id: str,
    notification_id: str,
) -> bool:
    """将单条通知标记为已读。返回是否找到并更新。"""
    r = await db.execute(
        update(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        .values(is_read=True)
    )
    await db.commit()
    return r.rowcount > 0


async def delete_notifications(
    db: AsyncSession,
    user_id: str,
    notification_ids: list[str] | None = None,
    delete_all: bool = False,
) -> int:
    """删除指定通知。返回删除条数。"""
    from sqlalchemy import delete

    if delete_all:
        r = await db.execute(
            delete(Notification).where(Notification.user_id == user_id)
        )
    elif notification_ids:
        r = await db.execute(
            delete(Notification).where(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
            )
        )
    else:
        return 0
    await db.commit()
    return r.rowcount
