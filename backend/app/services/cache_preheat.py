"""
缓存预热服务 - 应用启动时或定时预热热点数据
"""
from sqlalchemy import select, func
from typing import Dict, Any
from datetime import datetime, timedelta

from app.core.database import AsyncSession
from app.models.user import User
from app.models.post import Post
from app.models.membership import Membership, AppTheme
from app.core.cache import (
    PostCacheService,
    LikeCacheService,
)
# TODO: Fix missing imports - cache_service and UserCacheService don't exist
# from app.core.cache import (
#     cache_service,
#     UserCacheService,
#     PostCacheService,
#     LikeCacheService,
# )
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def preheat_hot_posts(db: AsyncSession, limit: int = 50) -> int:
    """
    预热热门帖子缓存
    获取近期高互动的帖子并缓存
    """
    seven_days_ago = datetime.now() - timedelta(days=7)

    result = await db.execute(
        select(Post)
        .where(Post.status == "normal", Post.created_at >= seven_days_ago)
        .order_by(
            Post.like_count.desc(),
            Post.comment_count.desc(),
            Post.view_count.desc(),
        )
        .limit(limit)
    )
    posts = result.scalars().all()

    count = 0
    for post in posts:
        try:
            # 缓存帖子详情
            cache_key = f"post:detail:{post.id}"
            post_data = {
                "id": post.id,
                "user_id": post.user_id,
                "content": post.content,
                "images": post.images,
                "type": post.type,
                "like_count": post.like_count,
                "comment_count": post.comment_count,
                "view_count": post.view_count,
                "created_at": post.created_at.isoformat() if post.created_at else None,
            }
            await cache_service.set(cache_key, post_data, ttl=3600)  # 1小时
            count += 1
        except Exception as e:
            logger.warning(f"Failed to cache post {post.id}: {e}")

    logger.info(f"Preheated {count} hot posts")
    return count


async def preheat_memberships(db: AsyncSession) -> int:
    """
    预热会员套餐缓存
    """
    result = await db.execute(
        select(Membership)
        .where(Membership.is_active == True)
        .order_by(Membership.sort_order)
    )
    memberships = result.scalars().all()

    count = 0
    for membership in memberships:
        try:
            cache_key = f"membership:detail:{membership.id}"
            membership_data = {
                "id": membership.id,
                "name": membership.name,
                "description": membership.description,
                "price": float(membership.price),
                "duration_days": membership.duration_days,
            }
            await cache_service.set(cache_key, membership_data, ttl=86400)  # 24小时
            count += 1
        except Exception as e:
            logger.warning(f"Failed to cache membership {membership.id}: {e}")

    logger.info(f"Preheated {count} memberships")
    return count


async def preheat_themes(db: AsyncSession) -> int:
    """
    预热主题缓存
    """
    result = await db.execute(
        select(AppTheme)
        .where(AppTheme.is_active == True)
        .order_by(AppTheme.sort_order)
    )
    themes = result.scalars().all()

    count = 0
    for theme in themes:
        try:
            cache_key = f"theme:detail:{theme.id}"
            theme_data = {
                "id": theme.id,
                "name": theme.name,
                "code": theme.code,
                "preview_image": theme.preview_image,
                "config": theme.config,
                "is_premium": theme.is_premium,
            }
            await cache_service.set(cache_key, theme_data, ttl=86400)  # 24小时
            count += 1
        except Exception as e:
            logger.warning(f"Failed to cache theme {theme.id}: {e}")

    logger.info(f"Preheated {count} themes")
    return count


async def preheat_statistics_data(db: AsyncSession) -> Dict[str, Any]:
    """
    预热统计数据缓存
    """
    from app.services.statistics_service import (
        get_insights_distributions,
        get_overview_stats,
    )

    try:
        # 预热概览统计
        overview = await get_overview_stats(db)
        await cache_service.set("stats:overview", overview, ttl=1800)  # 30分钟

        # 预热分布数据
        distributions = await get_insights_distributions(db)
        await cache_service.set("stats:distributions", distributions, ttl=3600)  # 1小时

        logger.info("Preheated statistics data")
        return {"overview": overview, "distributions": distributions}
    except Exception as e:
        logger.warning(f"Failed to cache statistics: {e}")
        return {}


async def preheat_all(db: AsyncSession) -> Dict[str, int]:
    """
    执行完整的缓存预热
    """
    logger.info("Starting cache preheating...")

    results = {}

    # 预热热门帖子
    results["hot_posts"] = await preheat_hot_posts(db)

    # 预热会员套餐
    results["memberships"] = await preheat_memberships(db)

    # 预热主题
    results["themes"] = await preheat_themes(db)

    # 预热统计数据
    await preheat_statistics_data(db)

    total = sum(results.values())
    logger.info(f"Cache preheating completed. Total: {total} items")

    return results
