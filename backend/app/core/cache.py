"""
Redis 缓存服务 - 使用原生 async Redis（redis-py 5.0+）
"""
from datetime import datetime
from typing import Optional, List
import redis.asyncio as aioredis
from .config import get_settings

settings = get_settings()

# Async Redis 客户端
redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """获取或创建 Redis 客户端连接池"""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return redis_client


async def close_redis():
    """关闭 Redis 连接"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


# 缓存 TTL 配置（保持不变）
USER_INFO_TTL = 3600
PAYDAY_STATUS_TTL = 86400
POST_HOT_TTL = 86400
POST_VIEW_TTL = 604800
LIKE_STATUS_TTL = 604800


def get_user_info_key(user_id: str) -> str:
    """用户信息缓存键"""
    return f"user:info:{user_id}"


def get_payday_status_key(user_id: str, date: str) -> str:
    """发薪日状态缓存键"""
    return f"payday:status:{user_id}:{date}"


def get_post_hot_key(date: str) -> str:
    """热门帖子 Sorted Set 键"""
    return f"post:hot:{date}"


def get_post_view_key(post_id: str) -> str:
    """帖子浏览计数键"""
    return f"post:view:{post_id}"


def get_like_status_key(user_id: str, target_type: str, target_id: str) -> str:
    """点赞状态键"""
    return f"like:status:{user_id}:{target_type}:{target_id}"


class PostCacheService:
    """帖子缓存服务 - 纯 async 实现"""

    @staticmethod
    async def add_to_hot_posts(post_id: str, score: float, date: Optional[str] = None) -> None:
        """添加帖子到热门列表"""
        client = await get_redis_client()
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        key = get_post_hot_key(date)
        await client.zadd(key, {post_id: score})
        await client.expire(key, POST_HOT_TTL)

    @staticmethod
    async def get_hot_posts(date: Optional[str] = None, start: int = 0, end: int = -1) -> List[str]:
        """获取热门帖子 ID 列表（按分数降序）"""
        client = await get_redis_client()
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        key = get_post_hot_key(date)
        return await client.zrevrange(key, start, end)

    @staticmethod
    async def remove_from_hot_posts(post_id: str, date: Optional[str] = None) -> None:
        """从热门列表移除帖子"""
        client = await get_redis_client()
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        key = get_post_hot_key(date)
        await client.zrem(key, post_id)

    @staticmethod
    async def increment_view_count(post_id: str) -> int:
        """增加帖子浏览量"""
        client = await get_redis_client()
        key = get_post_view_key(post_id)
        count = await client.incr(key)
        await client.expire(key, POST_VIEW_TTL)
        return count

    @staticmethod
    async def get_view_count(post_id: str) -> int:
        """获取帖子浏览量"""
        client = await get_redis_client()
        key = get_post_view_key(post_id)
        count = await client.get(key)
        return int(count) if count else 0


class LikeCacheService:
    """点赞缓存服务 - 纯 async 实现"""

    @staticmethod
    async def set_like_status(user_id: str, target_type: str, target_id: str) -> None:
        """设置点赞状态到缓存"""
        client = await get_redis_client()
        key = get_like_status_key(user_id, target_type, target_id)
        await client.set(key, "1", ex=LIKE_STATUS_TTL)

    @staticmethod
    async def remove_like_status(user_id: str, target_type: str, target_id: str) -> None:
        """移除点赞状态"""
        client = await get_redis_client()
        key = get_like_status_key(user_id, target_type, target_id)
        await client.delete(key)

    @staticmethod
    async def is_liked(user_id: str, target_type: str, target_id: str) -> bool:
        """检查是否已点赞（从缓存）"""
        client = await get_redis_client()
        key = get_like_status_key(user_id, target_type, target_id)
        return await client.exists(key) == 1


__all__ = [
    "get_redis_client",
    "close_redis",
    "get_user_info_key",
    "get_payday_status_key",
    "get_post_hot_key",
    "get_post_view_key",
    "get_like_status_key",
    "PostCacheService",
    "LikeCacheService",
    # 保持 TTL 常量
    "USER_INFO_TTL",
    "PAYDAY_STATUS_TTL",
    "POST_HOT_TTL",
    "POST_VIEW_TTL",
    "LIKE_STATUS_TTL",
]
