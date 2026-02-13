"""
内容推荐服务 - 基于协同过滤和热度推荐
"""
from __future__ import annotations

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.like import Like
from app.models.follow import Follow


async def recommend_posts_hot(
    db: AsyncSession, limit: int = 10
) -> list[Post]:
    """热门帖子推荐（基于点赞数、浏览数、评论数）。"""
    # 计算热度分数 = 点赞数 * 2 + 评论数 * 3 + 浏览数 * 0.1
    score_expr = (
        func.coalesce(Post.like_count, 0) * 2
        + func.coalesce(Post.comment_count, 0) * 3
        + func.coalesce(Post.view_count, 0) * 0.1
    )

    q = (
        select(Post)
        .where(
            Post.status == "normal",
            Post.risk_status == "approved",
        )
        .order_by(desc(score_expr))
        .limit(limit)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def recommend_posts_for_user(
    db: AsyncSession, user_id: str, limit: int = 20
) -> list[Post]:
    """基于协同过滤的用户推荐帖子。"""
    # 1. 获取用户关注的人
    follow_result = await db.execute(
        select(Follow.following_id)
        .where(Follow.follower_id == user_id)
    )
    following_ids = [row[0] for row in follow_result.fetchall()]

    if not following_ids:
        # 如果没有关注任何人，返回热门帖子
        return await recommend_posts_hot(db, limit)

    # 2. 获取关注用户的最近互动帖子（点赞、评论）
    # 简化版：获取关注用户发布的帖子
    from datetime import datetime, timedelta

    recent_days = 7  # 最近7天
    since_date = datetime.utcnow() - timedelta(days=recent_days)

    posts_result = await db.execute(
        select(Post)
        .where(
            Post.user_id.in_(following_ids),
            Post.status == "normal",
            Post.risk_status == "approved",
            Post.created_at >= since_date,
        )
        .order_by(desc(Post.created_at))
        .limit(limit * 2)
    )
    posts = list(posts_result.scalars().all())

    # 3. 获取用户已互动的帖子ID（排除已看过的）
    interacted_result = await db.execute(
        select(Like.target_id)
        .where(Like.user_id == user_id, Like.target_type == "post")
        .distinct()
    )
    interacted_ids = set(row[0] for row in interacted_result.fetchall())

    # 4. 过滤并排序返回推荐
    recommendations = [p for p in posts if p.id not in interacted_ids][:limit]
    return recommendations


async def recommend_topics(
    db: AsyncSession, limit: int = 10
) -> list[dict]:
    """推荐话题（按帖子数和活跃度排序）。"""
    from app.models.topic import Topic

    q = (
        select(Topic)
        .where(Topic.is_active == True)
        .order_by(desc(Topic.post_count), desc(Topic.sort_order))
        .limit(limit)
    )
    result = await db.execute(q)
    topics = list(result.scalars().all())

    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "cover_image": t.cover_image,
            "post_count": t.post_count,
        }
        for t in topics
    ]
