"""
分布式锁工具类

基于Redis实现的分布式锁，用于防止并发操作和重复提交。
支持异步上下文管理器模式，确保锁的自动释放。

使用示例:
    # 方式1: 上下文管理器（推荐）
    async with DistributedLock("resource:key", timeout=30) as lock:
        if lock.acquired:
            # 执行需要加锁的操作
            pass
        else:
            # 获取锁失败
            raise BusinessException("操作繁忙，请稍后再试")

    # 方式2: 手动控制
    lock = DistributedLock("resource:key")
    acquired = await lock.acquire()
    if acquired:
        try:
            # 执行操作
            pass
        finally:
            await lock.release()

    # 方式3: 幂等性检查
    async with IdempotencyCheck("order:user:123:product:456", ttl=60) as check:
        if check.is_duplicate:
            raise BusinessException("请勿重复提交")
        # 执行操作
"""
from contextlib import asynccontextmanager
from typing import Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.exceptions import BusinessException


class DistributedLock:
    """分布式锁

    基于Redis的SET NX EX命令实现的分布式锁。
    """

    def __init__(
        self,
        key: str,
        timeout: int = 30,
        prefix: str = "lock",
    ):
        """初始化分布式锁

        Args:
            key: 锁的唯一标识
            timeout: 锁的超时时间（秒），防止死锁
            prefix: Redis键前缀
        """
        self._key = f"{prefix}:{key}"
        self._timeout = timeout
        self._acquired = False
        self._client: Optional[redis.Redis] = None

    @property
    def acquired(self) -> bool:
        """是否已获取锁"""
        return self._acquired

    async def _get_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self._client is None:
            self._client = redis.from_url(settings.redis_url)
        return self._client

    async def acquire(self) -> bool:
        """尝试获取锁

        Returns:
            True表示获取成功，False表示锁已被占用
        """
        client = await self._get_client()
        # SET key value NX EX timeout
        # NX: 只在键不存在时设置
        # EX: 设置过期时间
        self._acquired = await client.set(
            self._key,
            "1",
            nx=True,
            ex=self._timeout
        )
        return self._acquired

    async def release(self) -> None:
        """释放锁"""
        if self._acquired and self._client:
            await self._client.delete(self._key)
            self._acquired = False

    async def close(self) -> None:
        """关闭Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None

    async def __aenter__(self) -> "DistributedLock":
        """异步上下文管理器入口"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        try:
            await self.release()
        finally:
            await self.close()


class IdempotencyCheck:
    """幂等性检查

    用于防止重复提交请求。
    """

    def __init__(
        self,
        key: str,
        ttl: int = 60,
        prefix: str = "idempotent",
    ):
        """初始化幂等性检查

        Args:
            key: 请求的唯一标识（建议使用客户端生成的UUID）
            ttl: 幂等性键的过期时间（秒）
            prefix: Redis键前缀
        """
        self._key = f"{prefix}:{key}"
        self._ttl = ttl
        self._is_duplicate = False
        self._client: Optional[redis.Redis] = None

    @property
    def is_duplicate(self) -> bool:
        """是否是重复请求"""
        return self._is_duplicate

    async def _get_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self._client is None:
            self._client = redis.from_url(settings.redis_url)
        return self._client

    async def check(self) -> bool:
        """检查是否是重复请求

        Returns:
            True表示是新请求（可以继续执行），False表示是重复请求
        """
        client = await self._get_client()
        # 尝试设置幂等性键
        was_set = await client.set(self._key, "1", nx=True, ex=self._ttl)
        self._is_duplicate = not was_set
        return was_set

    async def close(self) -> None:
        """关闭Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None

    async def __aenter__(self) -> "IdempotencyCheck":
        """异步上下文管理器入口"""
        await self.check()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close()


class CombinedLock:
    """组合锁（幂等性检查 + 分布式锁）

    同时提供幂等性检查和分布式锁功能。
    """

    def __init__(
        self,
        idempotency_key: str,
        lock_key: str,
        idempotency_ttl: int = 60,
        lock_timeout: int = 30,
    ):
        """初始化组合锁

        Args:
            idempotency_key: 幂等性检查的键
            lock_key: 分布式锁的键
            idempotency_ttl: 幂等性键过期时间（秒）
            lock_timeout: 锁超时时间（秒）
        """
        self._idempotency = IdempotencyCheck(idempotency_key, ttl=idempotency_ttl)
        self._lock = DistributedLock(lock_key, timeout=lock_timeout)
        self._client: Optional[redis.Redis] = None

    @property
    def is_duplicate(self) -> bool:
        """是否是重复请求"""
        return self._idempotency.is_duplicate

    @property
    def lock_acquired(self) -> bool:
        """是否已获取锁"""
        return self._lock.acquired

    async def acquire(self) -> tuple[bool, bool]:
        """尝试获取组合锁

        Returns:
            (幂等性检查通过, 锁获取成功)
        """
        # 先进行幂等性检查
        idempotency_passed = await self._idempotency.check()
        if not idempotency_passed:
            return False, False

        # 再获取分布式锁
        lock_acquired = await self._lock.acquire()
        return True, lock_acquired

    async def release(self) -> None:
        """释放锁（幂等性键不释放，保持防重复效果）"""
        await self._lock.release()

    async def close(self) -> None:
        """关闭连接"""
        await self._idempotency.close()
        await self._lock.close()

    async def __aenter__(self) -> "CombinedLock":
        """异步上下文管理器入口"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        try:
            await self.release()
        finally:
            await self.close()


@asynccontextmanager
async def with_distributed_lock(
    key: str,
    timeout: int = 30,
    error_message: str = "操作繁忙，请稍后再试",
    error_code: str = "LOCK_ACQUIRE_FAILED",
):
    """分布式锁上下文管理器（简化版）

    使用示例:
        async with with_distributed_lock("user:123:order") as acquired:
            if not acquired:
                raise BusinessException(error_message, code=error_code)
            # 执行需要加锁的操作
    """
    lock = DistributedLock(key, timeout=timeout)
    try:
        acquired = await lock.acquire()
        yield acquired
    finally:
        await lock.release()
        await lock.close()


@asynccontextmanager
async def with_idempotency_check(
    key: str,
    ttl: int = 60,
    error_message: str = "请勿重复提交",
    error_code: str = "DUPLICATE_REQUEST",
):
    """幂等性检查上下文管理器（简化版）

    使用示例:
        async with with_idempotency_check("order:123") as is_new:
            if not is_new:
                raise BusinessException(error_message, code=error_code)
            # 执行操作
    """
    check = IdempotencyCheck(key, ttl=ttl)
    try:
        is_new = await check.check()
        yield is_new
    finally:
        await check.close()
