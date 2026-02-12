"""
速率限制 - 使用 Redis 实现 API 访问频率限制
防止 DDoS 和滥用
"""
import time
from typing import Optional, Dict
from collections import defaultdict, deque
from datetime import datetime

from fastapi import HTTPException, Request, status
from app.core.cache import get_redis_client
from app.core.exceptions import RateLimitException
from app.utils.request import get_client_ip


class RateLimiter:
    """速率限制器（Redis主 + 内存后备）"""

    def __init__(
        self,
        times: int = 60,      # 时间窗口（秒）
        max_requests: int = 100,  # 最大请求数
    ):
        self.times = times
        self.max_requests = max_requests
        # 内存后备：{key: deque([timestamp1, timestamp2, ...])}
        self._fallback_store: Dict[str, deque] = defaultdict(lambda: deque())

    def _cleanup_fallback(self, key: str) -> None:
        """清理内存后备中过期的请求记录"""
        now = time.time()
        cutoff = now - self.times
        # 移除时间窗口外的记录
        while self._fallback_store[key] and self._fallback_store[key][0] < cutoff:
            self._fallback_store[key].popleft()

    def _check_fallback(self, key: str) -> bool:
        """检查内存后备中的速率限制"""
        self._cleanup_fallback(key)
        return len(self._fallback_store[key]) < self.max_requests

    def _record_fallback(self, key: str) -> None:
        """在内存后备中记录请求"""
        self._fallback_store[key].append(time.time())

    async def check(
        self,
        key: str,
        request: Request,
    ) -> None:
        """
        检查速率限制（Redis主 + 内存后备）

        Args:
            key: 限制键（如用户ID、IP地址）
            request: FastAPI 请求对象

        Raises:
            RateLimitException: 超出速率限制
        """
        redis = await get_redis_client()

        # Redis 键：rate_limit:{key}
        redis_key = f"rate_limit:{key}"

        if redis:
            try:
                # 获取当前计数
                current = await redis.get(redis_key)
                current = int(current) if current else 0

                if current >= self.max_requests:
                    # 获取过期时间
                    ttl = await redis.ttl(redis_key)
                    raise RateLimitException(
                        f"请求过于频繁，请在 {ttl} 秒后重试",
                        details={
                            "limit": self.max_requests,
                            "window": self.times,
                            "retry_after": ttl,
                        }
                    )

                # 增加计数
                pipe = redis.pipeline()
                pipe.incr(redis_key)
                pipe.expire(redis_key, self.times)
                await pipe.execute()
                return  # Redis 正常工作，直接返回

            except Exception as e:
                # Redis 故障，降级到内存限流
                from app.utils.logger import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Rate limiter Redis error, using fallback: {e}")

        # Redis 不可用，使用内存后备
        if not self._check_fallback(key):
            raise RateLimitException(
                f"请求过于频繁（限流服务降级中）",
                details={
                    "limit": self.max_requests,
                    "window": self.times,
                    "retry_after": self.times,
                    "fallback": True,
                }
            )
        self._record_fallback(key)


async def get_client_identifier(request: Request) -> str:
    """
    获取客户端标识符（用于速率限制）

    优先级: 用户ID > IP地址 > 未知

    Args:
        request: FastAPI 请求对象

    Returns:
        客户端标识字符串
    """
    # 获取客户端 IP（使用通用工具函数）
    client_ip = get_client_ip(request)

    return f"ip:{client_ip}"


# 预定义的速率限制规则
# 一般 API: 100次/分钟
RATE_LIMIT_GENERAL = RateLimiter(times=60, max_requests=100)

# 登录 API: 5次/分钟
RATE_LIMIT_LOGIN = RateLimiter(times=60, max_requests=5)

# 发帖 API: 10次/分钟
RATE_LIMIT_POST = RateLimiter(times=60, max_requests=10)

# 评论 API: 20次/分钟
RATE_LIMIT_COMMENT = RateLimiter(times=60, max_requests=20)
