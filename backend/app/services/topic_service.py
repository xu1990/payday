"""
话题服务 - CRUD、列表、启用/禁用
"""
from __future__ import annotations

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic


async def create_topic(
    db: AsyncSession,
    name: str,
    description: str | None = None,
    cover_image: str | None = None,
    sort_order: int = 0,
) -> Topic:
    """创建话题。"""
    topic = Topic(
        name=name,
        description=description,
        cover_image=cover_image,
        sort_order=sort_order,
    )
    db.add(topic)
    await db.flush()
    await db.refresh(topic)
    return topic


async def get_topic_by_id(db: AsyncSession, topic_id: str) -> Topic | None:
    """获取单个话题。"""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    return result.scalar_one_or_none()


async def list_topics(
    db: AsyncSession,
    active_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[Topic], int]:
    """获取话题列表（按排序权重、创建时间倒序）。"""
    q = select(Topic)
    if active_only:
        q = q.where(Topic.is_active == True)
    count_q = select(func.count()).select_from(Topic)
    if active_only:
        count_q = count_q.where(Topic.is_active == True)

    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(Topic.sort_order.desc(), Topic.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def update_topic(
    db: AsyncSession,
    topic_id: str,
    name: str | None = None,
    description: str | None = None,
    cover_image: str | None = None,
    is_active: bool | None = None,
    sort_order: int | None = None,
) -> Topic | None:
    """更新话题。"""
    topic = await get_topic_by_id(db, topic_id)
    if not topic:
        return None

    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if cover_image is not None:
        update_data["cover_image"] = cover_image
    if is_active is not None:
        update_data["is_active"] = is_active
    if sort_order is not None:
        update_data["sort_order"] = sort_order

    if update_data:
        await db.execute(
            update(Topic).where(Topic.id == topic_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(topic)

    return topic


async def delete_topic(db: AsyncSession, topic_id: str) -> bool:
    """删除话题。"""
    from sqlalchemy import delete

    result = await db.execute(delete(Topic).where(Topic.id == topic_id))
    await db.commit()
    return result.rowcount > 0


async def increment_post_count(db: AsyncSession, topic_id: str) -> bool:
    """增加话题帖子计数。"""
    result = await db.execute(
        update(Topic)
        .where(Topic.id == topic_id)
        .values(post_count=Topic.post_count + 1)
    )
    await db.commit()
    return result.rowcount > 0


async def decrement_post_count(db: AsyncSession, topic_id: str) -> bool:
    """减少话题帖子计数。"""
    result = await db.execute(
        update(Topic)
        .where(Topic.id == topic_id)
        .values(post_count=func.max(Topic.post_count - 1, 0))
    )
    await db.commit()
    return result.rowcount > 0
