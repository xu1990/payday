"""
Redis 缓存服务 - 技术方案 2.3

NOTE: 当前使用同步Redis客户端。在生产环境中，为获得更好的性能，
建议升级到 redis.asyncio (redis-py 4.2+)
"""
from datetime import datetime, timedelta
from typing import Optional, List
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import asyncio
import redis
from .config import get_settings

settings = get_settings()

# Redis 连接池
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
    max_connections=50,
)
redis_client = redis.Redis(connection_pool=redis_pool)

# 线程池用于包装同步Redis调用
_redis_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="redis_")


def _run_in_thread(func):
    """装饰器：在线程池中运行同步Redis函数，避免阻塞事件循环"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_redis_executor, func, *args, **kwargs)
    return wrapper


# 缓存 TTL 配置
USER_INFO_TTL = 3600  # 用户信息缓存 1 小时
PAYDAY_STATUS_TTL = 86400  # 发薪日状态缓存 1 天
POST_HOT_TTL = 86400  # 热门帖子缓存 1 天
POST_VIEW_TTL = 604800  # 浏览计数缓存 7 天
LIKE_STATUS_TTL = 604800  # 点赞状态缓存 7 天


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
    """帖子缓存服务 - 与技术方案 2.3 一致"""

    @staticmethod
    @_run_in_thread
    def _add_to_hot_posts_sync(post_id: str, score: float, date: str) -> None:
        """同步：添加帖子到热门列表"""
        key = get_post_hot_key(date)
        redis_client.zadd(key, {post_id: score})
        redis_client.expire(key, POST_HOT_TTL)

    @staticmethod
    async def add_to_hot_posts(post_id: str, score: float, date: Optional[str] = None) -> None:
        """添加帖子到热门列表（ZSet）"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        await PostCacheService._add_to_hot_posts_sync(post_id, score, date)

    @staticmethod
    @_run_in_thread
    def _get_hot_posts_sync(date: str, start: int, end: int) -> List[str]:
        """同步：获取热门帖子列表"""
        key = get_post_hot_key(date)
        return redis_client.zrevrange(key, start, end)

    @staticmethod
    async def get_hot_posts(date: Optional[str] = None, start: int = 0, end: int = -1) -> List[str]:
        """获取热门帖子 ID 列表（按分数降序）"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return await PostCacheService._get_hot_posts_sync(date, start, end)

    @staticmethod
    @_run_in_thread
    def _remove_from_hot_posts_sync(post_id: str, date: str) -> None:
        """同步：从热门列表移除帖子"""
        key = get_post_hot_key(date)
        redis_client.zrem(key, post_id)

    @staticmethod
    async def remove_from_hot_posts(post_id: str, date: Optional[str] = None) -> None:
        """从热门列表移除帖子"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        await PostCacheService._remove_from_hot_posts_sync(post_id, date)

    @staticmethod
    @_run_in_thread
    def _increment_view_count_sync(post_id: str) -> int:
        """同步：增加帖子浏览量"""
        key = get_post_view_key(post_id)
        count = redis_client.incr(key)
        redis_client.expire(key, POST_VIEW_TTL)
        return count

    @staticmethod
    async def increment_view_count(post_id: str) -> int:
        """增加帖子浏览量"""
        return await PostCacheService._increment_view_count_sync(post_id)

    @staticmethod
    @_run_in_thread
    def _get_view_count_sync(post_id: str) -> int:
        """同步：获取帖子浏览量"""
        key = get_post_view_key(post_id)
        count = redis_client.get(key)
        return int(count) if count else 0

    @staticmethod
    async def get_view_count(post_id: str) -> int:
        """获取帖子浏览量"""
        return await PostCacheService._get_view_count_sync(post_id)


class LikeCacheService:
    """点赞缓存服务 - 与技术方案 2.3 一致"""

    @staticmethod
    @_run_in_thread
    def _set_like_status_sync(user_id: str, target_type: str, target_id: str) -> None:
        """同步：设置点赞状态"""
        key = get_like_status_key(user_id, target_type, target_id)
        redis_client.set(key, "1", ex=LIKE_STATUS_TTL)

    @staticmethod
    async def set_like_status(user_id: str, target_type: str, target_id: str) -> None:
        """设置点赞状态到缓存"""
        await LikeCacheService._set_like_status_sync(user_id, target_type, target_id)

    @staticmethod
    @_run_in_thread
    def _remove_like_status_sync(user_id: str, target_type: str, target_id: str) -> None:
        """同步：移除点赞状态"""
        key = get_like_status_key(user_id, target_type, target_id)
        redis_client.delete(key)

    @staticmethod
    async def remove_like_status(user_id: str, target_type: str, target_id: str) -> None:
        """移除点赞状态"""
        await LikeCacheService._remove_like_status_sync(user_id, target_type, target_id)

    @staticmethod
    @_run_in_thread
    def _is_liked_sync(user_id: str, target_type: str, target_id: str) -> bool:
        """同步：检查是否已点赞"""
        key = get_like_status_key(user_id, target_type, target_id)
        return redis_client.exists(key) == 1

    @staticmethod
    async def is_liked(user_id: str, target_type: str, target_id: str) -> bool:
        """检查是否已点赞（从缓存）"""
        return await LikeCacheService._is_liked_sync(user_id, target_type, target_id)


__all__ = [
    "redis_client",
    "get_user_info_key",
    "get_payday_status_key",
    "get_post_hot_key",
    "get_post_view_key",
    "get_like_status_key",
    "PostCacheService",
    "LikeCacheService",
    "USER_INFO_TTL",
    "PAYDAY_STATUS_TTL",
    "POST_HOT_TTL",
    "POST_VIEW_TTL",
    "LIKE_STATUS_TTL",
]
