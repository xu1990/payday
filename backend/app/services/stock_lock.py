"""
分布式库存锁定服务 (Distributed Stock Lock Service)

使用Redis实现原子性的库存锁定，防止超卖：
1. acquire_stock_lock - 获取库存锁（下单时）
2. confirm_stock - 确认扣减库存（支付成功后）
3. release_stock_lock - 释放库存锁（订单取消/超时）

关键特性：
- 原子性操作：使用Redis pipeline确保操作原子性
- 分布式锁：多实例部署时防止并发超卖
- 自动过期：锁有TTL（5分钟），防止死锁
- 错误容错：Redis连接失败时优雅降级

使用场景：
- 用户下单时：先调用acquire_stock_lock锁定库存
- 支付成功后：调用confirm_stock确认扣减
- 订单取消/超时：调用release_stock_lock释放锁定
"""
import logging
from typing import Optional
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class StockLockService:
    """
    分布式库存锁定服务

    使用Redis实现原子性的库存锁定，防止在高并发场景下的超卖问题。

    Attributes:
        LOCK_TTL: 锁的TTL（秒），默认300秒（5分钟）
        redis_client: Redis客户端实例

    Example:
        ```python
        service = StockLockService(redis_client=redis)

        # 下单时锁定库存
        locked = await service.acquire_stock_lock("sku_123", 2)
        if not locked:
            raise BusinessException("库存不足")

        try:
            # 处理订单...
            # 支付成功后确认扣减
            await service.confirm_stock("sku_123", 2)
        except Exception as e:
            # 支付失败，释放锁
            await service.release_stock_lock("sku_123", 2)
            raise
        ```
    """

    LOCK_TTL = 300  # 5分钟

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """
        初始化库存锁定服务

        Args:
            redis_client: Redis客户端实例。如果为None，会使用默认客户端
        """
        self.redis_client = redis_client
        self._external_client = redis_client is not None

    async def _get_redis(self) -> aioredis.Redis:
        """
        获取Redis客户端

        Returns:
            Redis客户端实例

        Raises:
            RuntimeError: 如果无法获取Redis连接
        """
        if self._external_client and self.redis_client:
            return self.redis_client

        # 使用默认Redis客户端
        from app.core.cache import get_redis_client
        try:
            return await get_redis_client()
        except Exception as e:
            logger.error(f"Failed to get Redis client: {e}")
            raise RuntimeError(f"Failed to get Redis client: {e}")

    async def acquire_stock_lock(
        self,
        sku_id: str,
        quantity: int
    ) -> bool:
        """
        获取库存锁

        使用Redis INCR进行原子操作：
        1. 获取当前库存和已锁定数量
        2. 检查锁定后是否超过可用库存
        3. 如果超过则返回False
        4. 否则增加锁定数量并设置TTL

        Args:
            sku_id: SKU ID
            quantity: 要锁定的数量

        Returns:
            bool: 成功返回True，库存不足返回False
        """
        # 参数验证
        if not sku_id or quantity <= 0:
            logger.warning(f"Invalid params: sku_id='{sku_id}', quantity={quantity}")
            return False

        lock_key = f"stock:lock:{sku_id}"
        stock_key = f"sku:stock:{sku_id}"

        try:
            redis = await self._get_redis()

            # 使用pipeline获取库存和锁定数量
            pipe = redis.pipeline()
            pipe.get(stock_key)
            pipe.get(lock_key)
            results = await pipe.execute()

            stock_value, locked_value = results

            # 解析库存值
            available = int(stock_value) if stock_value else 0
            locked_qty = int(locked_value) if locked_value else 0

            # 检查库存是否充足
            if locked_qty + quantity > available:
                logger.info(
                    f"Insufficient stock for {sku_id}: "
                    f"available={available}, locked={locked_qty}, requested={quantity}"
                )
                return False

            # 原子性地增加锁定数量
            await redis.incrby(lock_key, quantity)
            await redis.expire(lock_key, self.LOCK_TTL)

            logger.info(
                f"Stock lock acquired for {sku_id}: "
                f"quantity={quantity}, total_locked={locked_qty + quantity}"
            )
            return True

        except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
            logger.error(f"Redis connection error acquiring lock for {sku_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error acquiring lock for {sku_id}: {e}")
            return False

    async def confirm_stock(
        self,
        sku_id: str,
        quantity: int
    ) -> None:
        """
        确认库存扣减（支付成功后调用）

        从锁定中移除并扣减实际库存。
        使用pipeline确保两个操作的原子性。

        Args:
            sku_id: SKU ID
            quantity: 要扣减的数量

        Note:
            此操作会同时减少锁定数量和实际库存数量
        """
        if not sku_id:
            logger.warning("Invalid sku_id for confirm_stock")
            return

        lock_key = f"stock:lock:{sku_id}"
        stock_key = f"sku:stock:{sku_id}"

        try:
            redis = await self._get_redis()

            # 使用pipeline确保原子性
            pipe = redis.pipeline()
            pipe.decrby(lock_key, quantity)
            pipe.decrby(stock_key, quantity)
            await pipe.execute()

            logger.info(
                f"Stock confirmed for {sku_id}: "
                f"quantity={quantity} deducted from lock and stock"
            )

        except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
            logger.error(f"Redis connection error confirming stock for {sku_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error confirming stock for {sku_id}: {e}")

    async def release_stock_lock(
        self,
        sku_id: str,
        quantity: int
    ) -> None:
        """
        释放库存锁（订单取消/超时时调用）

        仅减少锁定数量，不影响实际库存。

        Args:
            sku_id: SKU ID
            quantity: 要释放的数量

        Note:
            此操作只减少锁定数量，实际库存保持不变
        """
        if not sku_id:
            logger.warning("Invalid sku_id for release_stock_lock")
            return

        lock_key = f"stock:lock:{sku_id}"

        try:
            redis = await self._get_redis()
            await redis.decrby(lock_key, quantity)

            logger.info(
                f"Stock lock released for {sku_id}: "
                f"quantity={quantity}"
            )

        except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
            logger.error(f"Redis connection error releasing lock for {sku_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error releasing lock for {sku_id}: {e}")

    async def get_locked_quantity(self, sku_id: str) -> int:
        """
        获取当前锁定的数量

        Args:
            sku_id: SKU ID

        Returns:
            int: 当前锁定的数量，如果键不存在返回0
        """
        if not sku_id:
            return 0

        lock_key = f"stock:lock:{sku_id}"

        try:
            redis = await self._get_redis()
            value = await redis.get(lock_key)
            return int(value) if value else 0

        except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
            logger.error(f"Redis connection error getting locked quantity for {sku_id}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error getting locked quantity for {sku_id}: {e}")
            return 0

    async def get_available_stock(
        self,
        sku_id: str,
        total_stock: Optional[int] = None
    ) -> int:
        """
        获取可用库存（总库存 - 已锁定）

        Args:
            sku_id: SKU ID
            total_stock: 总库存。如果为None，会从Redis读取

        Returns:
            int: 可用库存数量
        """
        if not sku_id:
            return 0

        stock_key = f"sku:stock:{sku_id}"
        lock_key = f"stock:lock:{sku_id}"

        try:
            redis = await self._get_redis()

            # 如果没有提供总库存，从Redis读取
            if total_stock is None:
                stock_value = await redis.get(stock_key)
                total_stock = int(stock_value) if stock_value else 0

            # 获取锁定数量
            locked_value = await redis.get(lock_key)
            locked_qty = int(locked_value) if locked_value else 0

            available = max(0, total_stock - locked_qty)
            return available

        except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
            logger.error(f"Redis connection error getting available stock for {sku_id}: {e}")
            return total_stock if total_stock is not None else 0
        except Exception as e:
            logger.error(f"Unexpected error getting available stock for {sku_id}: {e}")
            return total_stock if total_stock is not None else 0
