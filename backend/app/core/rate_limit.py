"""
速率限制 - 使用 Redis 实现 API 访问频率限制
防止 DDoS 和滥用
"""
import time
from typing import Optional

from fastapi import HTTPException, Request, status
from app.core.cache import get_redis_client
from app.core.exceptions import RateLimitException


class RateLimiter:
    """速率限制器"""

    def __init__(
        self,
        times: int = 60,      # 时间窗口（秒）
        max_requests: int = 100,  # 最大请求数
    ):
        self.times = times
        self.max_requests = max_requests

    async def check(
        self,
        key: str,
        request: Request,
    ) -> None:
        """
        检查速率限制

        Args:
            key: 限制键（如用户ID、IP地址）
            request: FastAPI 请求对象

        Raises:
            RateLimitException: 超出速率限制
        """
        redis = await get_redis_client()

        # Redis 键：rate_limit:{key}
        redis_key = f"rate_limit:{key}"

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

        except Exception as e:
            # Redis 故障时记录日志但不限制请求
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Rate limiter Redis error: {e}")


async def get_client_identifier(request: Request) -> str:
    """
    获取客户端标识符（用于速率限制）

    优先级: 用户ID > IP地址 > 未知

    Args:
        request: FastAPI 请求对象

    Returns:
        客户端标识字符串
    """
    # 尝试从请求中获取用户ID（如果已认证）
    # 注意：这里简化处理，实际应从 token 解析
    # 为了避免重复解析 token，使用 IP 地址

    # 获取客户端 IP
    client_ip = _get_client_ip(request)

    return f"ip:{client_ip}"


def _get_client_ip(request: Request) -> str:
    """从请求中获取客户端 IP"""
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


# 预定义的速率限制规则
# 一般 API: 100次/分钟
RATE_LIMIT_GENERAL = RateLimiter(times=60, max_requests=100)

# 登录 API: 5次/分钟
RATE_LIMIT_LOGIN = RateLimiter(times=60, max_requests=5)

# 发帖 API: 10次/分钟
RATE_LIMIT_POST = RateLimiter(times=60, max_requests=10)

# 评论 API: 20次/分钟
RATE_LIMIT_COMMENT = RateLimiter(times=60, max_requests=20)
