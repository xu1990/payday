"""
帖子服务 - 发帖、列表（热门/最新）、详情；管理端列表/状态/删除；与技术方案 2.2、3.3.1 一致
"""
from typing import List, Literal, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.schemas.post import PostCreate


async def create(
    db: AsyncSession,
    user_id: str,
    data: PostCreate,
    *,
    anonymous_name: str,
) -> Post:
    post = Post(
        user_id=user_id,
        anonymous_name=anonymous_name,
        content=data.content,
        images=data.images,
        tags=data.tags,
        type=data.type,
        salary_range=data.salary_range,
        industry=data.industry,
        city=data.city,
        status="normal",
        risk_status="pending",
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def get_by_id(
    db: AsyncSession,
    post_id: str,
    only_approved: bool = True,
) -> Optional[Post]:
    q = select(Post).where(Post.id == post_id, Post.status == "normal")
    if only_approved:
        q = q.where(Post.risk_status == "approved")
    result = await db.execute(q)
    return result.scalar_one_or_none()


async def list_posts(
    db: AsyncSession,
    sort: Literal["hot", "latest"] = "latest",
    limit: int = 20,
    offset: int = 0,
) -> List[Post]:
    q = (
        select(Post)
        .where(Post.status == "normal", Post.risk_status == "approved")
        .limit(limit)
        .offset(offset)
    )
    if sort == "hot":
        q = q.order_by(Post.like_count.desc(), Post.created_at.desc())
    else:
        q = q.order_by(Post.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_posts_for_admin(
    db: AsyncSession,
    status: Optional[str] = None,
    risk_status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Post], int]:
    """管理端帖子列表：可选按 status、risk_status 筛选，返回列表与总数"""
    base = select(Post)
    count_base = select(func.count()).select_from(Post)
    if status:
        base = base.where(Post.status == status)
        count_base = count_base.where(Post.status == status)
    if risk_status:
        base = base.where(Post.risk_status == risk_status)
        count_base = count_base.where(Post.risk_status == risk_status)
    total = (await db.execute(count_base)).scalar() or 0
    q = base.order_by(Post.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_by_id_for_admin(db: AsyncSession, post_id: str) -> Optional[Post]:
    """管理端取帖子详情（不限制 status/risk_status）"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    return result.scalar_one_or_none()


async def update_post_status_for_admin(
    db: AsyncSession,
    post_id: str,
    *,
    status: Optional[str] = None,
    risk_status: Optional[str] = None,
    risk_reason: Optional[str] = None,
) -> Optional[Post]:
    """管理端更新帖子状态（status 隐藏/恢复/删除）或风控人工通过/拒绝"""
    post = await get_by_id_for_admin(db, post_id)
    if not post:
        return None
    if status is not None:
        post.status = status
    if risk_status is not None:
        post.risk_status = risk_status
    if risk_reason is not None:
        post.risk_reason = risk_reason
    await db.commit()
    await db.refresh(post)
    return post


async def delete_post_for_admin(db: AsyncSession, post_id: str) -> bool:
    """管理端删除帖子（软删：status=deleted）"""
    post = await get_by_id_for_admin(db, post_id)
    if not post:
        return False
    post.status = "deleted"
    await db.commit()
    return True
