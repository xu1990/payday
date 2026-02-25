"""
Stock Lock Service 测试 - 分布式库存锁定服务

测试覆盖：
1. acquire_stock_lock - 获取库存锁
2. confirm_stock - 确认扣减库存
3. release_stock_lock - 释放库存锁
4. 并发锁竞争
5. TTL过期
6. 错误处理
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
import redis.asyncio as aioredis
from app.services.stock_lock import StockLockService


def create_mock_redis_pipeline(stock_value=None, locked_value=None):
    """
    创建mock Redis pipeline

    Args:
        stock_value: 库存值
        locked_value: 锁定值

    Returns:
        tuple: (mock_redis, mock_pipeline)
    """
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.setex = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.incr = AsyncMock()
    mock_redis.decr = AsyncMock()
    mock_redis.incrby = AsyncMock()
    mock_redis.decrby = AsyncMock()
    mock_redis.expire = AsyncMock()
    mock_redis.zadd = AsyncMock()
    mock_redis.zrevrange = AsyncMock()
    mock_redis.exists = AsyncMock()
    mock_redis.eval = AsyncMock()  # For Lua script execution

    # 创建pipeline mock
    mock_pipeline = MagicMock()
    mock_pipeline.get = mock_redis.get
    mock_pipeline.execute = AsyncMock(return_value=[stock_value, locked_value])
    mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

    return mock_redis


class TestAcquireStockLock:
    """测试获取库存锁"""

    @pytest.mark.asyncio
    async def test_acquire_lock_with_sufficient_stock(self):
        """测试库存充足时成功获取锁"""
        mock_redis = create_mock_redis_pipeline("100", "0")
        mock_redis.eval = AsyncMock(return_value=1)  # Lua script returns 1 for success

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=5)

        assert result is True
        mock_redis.eval.assert_called_once()
        # Verify the call arguments
        call_args = mock_redis.eval.call_args
        assert call_args[0][0].strip().startswith("local stock")  # Lua script
        assert call_args[0][1] == 2  # Number of keys
        assert call_args[0][2] == "sku:stock:sku_123"  # KEYS[1]
        assert call_args[0][3] == "stock:lock:sku_123"  # KEYS[2]
        assert call_args[0][4] == 5  # ARGV[1] - quantity
        assert call_args[0][5] == 300  # ARGV[2] - TTL

    @pytest.mark.asyncio
    async def test_acquire_lock_with_insufficient_stock(self):
        """测试库存不足时获取锁失败"""
        mock_redis = create_mock_redis_pipeline("10", "8")
        mock_redis.eval = AsyncMock(return_value=0)  # Lua script returns 0 for failure

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=5)

        assert result is False
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_lock_exactly_available(self):
        """测试库存刚好足够"""
        mock_redis = create_mock_redis_pipeline("10", "0")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=10)

        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_lock_exceeds_by_one(self):
        """测试库存差1个不足"""
        mock_redis = create_mock_redis_pipeline("10", "0")
        mock_redis.eval = AsyncMock(return_value=0)

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=11)

        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_lock_with_existing_locks(self):
        """测试已有部分锁定时获取锁"""
        mock_redis = create_mock_redis_pipeline("100", "50")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=30)

        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_lock_no_existing_stock_key(self):
        """测试SKU库存不存在"""
        mock_redis = create_mock_redis_pipeline(None, "0")
        mock_redis.eval = AsyncMock(return_value=0)

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=5)

        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_lock_no_existing_lock_key(self):
        """测试锁定键不存在"""
        mock_redis = create_mock_redis_pipeline("100", None)
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=5)

        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_lock_sets_ttl(self):
        """测试设置锁TTL"""
        mock_redis = create_mock_redis_pipeline("100", "0")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)
        await service.acquire_stock_lock(sku_id="sku_123", quantity=5)

        # 验证eval被调用，且TTL参数为300
        call_args = mock_redis.eval.call_args
        assert call_args[0][5] == 300  # ARGV[2] - TTL

    @pytest.mark.asyncio
    async def test_acquire_lock_zero_quantity(self):
        """测试请求0数量"""
        mock_redis = create_mock_redis_pipeline("100", "0")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=0)

        assert result is False  # quantity <= 0 should return False
        # eval should not be called for invalid input
        mock_redis.eval.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_lock_negative_quantity(self):
        """测试负数数量（应该失败）"""
        mock_redis = create_mock_redis_pipeline("100", "0")

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=-5)

        assert result is False
        mock_redis.eval.assert_not_called()


class TestConfirmStock:
    """测试确认扣减库存"""

    @pytest.mark.asyncio
    async def test_confirm_stock_deducts_from_lock_and_stock(self):
        """测试确认扣减：减少锁定和实际库存"""
        mock_redis = create_mock_redis_pipeline(None, None)
        mock_redis.decrby = AsyncMock(return_value=0)

        # 创建pipeline mock
        mock_pipeline = MagicMock()
        mock_pipeline.decrby = mock_redis.decrby
        mock_pipeline.execute = AsyncMock(return_value=[None, None])
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

        service = StockLockService(redis_client=mock_redis)
        await service.confirm_stock(sku_id="sku_123", quantity=5)

        # 验证调用了两次decrby
        assert mock_redis.decrby.call_count == 2
        calls = mock_redis.decrby.call_args_list

        # 第一次：减少锁定数量
        assert calls[0][0][0] == "stock:lock:sku_123"
        assert calls[0][0][1] == 5

        # 第二次：减少实际库存
        assert calls[1][0][0] == "sku:stock:sku_123"
        assert calls[1][0][1] == 5

    @pytest.mark.asyncio
    async def test_confirm_stock_large_quantity(self):
        """测试大批量扣减"""
        mock_redis = create_mock_redis_pipeline(None, None)
        mock_redis.decrby = AsyncMock(return_value=0)

        mock_pipeline = MagicMock()
        mock_pipeline.decrby = mock_redis.decrby
        mock_pipeline.execute = AsyncMock(return_value=[None, None])
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

        service = StockLockService(redis_client=mock_redis)
        await service.confirm_stock(sku_id="sku_123", quantity=1000)

        assert mock_redis.decrby.call_count == 2

    @pytest.mark.asyncio
    async def test_confirm_stock_zero_quantity(self):
        """测试确认0数量"""
        mock_redis = create_mock_redis_pipeline(None, None)
        mock_redis.decrby = AsyncMock(return_value=0)

        mock_pipeline = MagicMock()
        mock_pipeline.decrby = mock_redis.decrby
        mock_pipeline.execute = AsyncMock(return_value=[None, None])
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

        service = StockLockService(redis_client=mock_redis)
        await service.confirm_stock(sku_id="sku_123", quantity=0)

        assert mock_redis.decrby.call_count == 2


class TestReleaseStockLock:
    """测试释放库存锁"""

    @pytest.mark.asyncio
    async def test_release_lock_reduces_locked_quantity(self):
        """测试释放锁减少锁定数量"""
        mock_redis = create_mock_redis_pipeline(None, None)
        mock_redis.decrby = AsyncMock(return_value=0)

        service = StockLockService(redis_client=mock_redis)
        await service.release_stock_lock(sku_id="sku_123", quantity=5)

        mock_redis.decrby.assert_called_once_with("stock:lock:sku_123", 5)

    @pytest.mark.asyncio
    async def test_release_lock_multiple_times(self):
        """测试多次释放锁"""
        mock_redis = create_mock_redis_pipeline(None, None)
        mock_redis.decrby = AsyncMock(return_value=0)

        service = StockLockService(redis_client=mock_redis)

        await service.release_stock_lock(sku_id="sku_123", quantity=3)
        await service.release_stock_lock(sku_id="sku_123", quantity=2)

        assert mock_redis.decrby.call_count == 2

    @pytest.mark.asyncio
    async def test_release_lock_zero_quantity(self):
        """测试释放0数量"""
        mock_redis = create_mock_redis_pipeline(None, None)
        mock_redis.decrby = AsyncMock(return_value=0)

        service = StockLockService(redis_client=mock_redis)
        await service.release_stock_lock(sku_id="sku_123", quantity=0)

        mock_redis.decrby.assert_called_once_with("stock:lock:sku_123", 0)


class TestConcurrentLockAttempts:
    """测试并发锁竞争"""

    @pytest.mark.asyncio
    async def test_concurrent_locks_first_wins(self):
        """测试并发锁：先到先得"""
        # 第一次请求：库存100，锁定0 -> 成功锁定20
        mock_redis = create_mock_redis_pipeline("100", "0")
        mock_redis.eval = AsyncMock(return_value=1)  # First request succeeds

        service = StockLockService(redis_client=mock_redis)

        # 第一次请求20个
        result1 = await service.acquire_stock_lock(sku_id="sku_123", quantity=20)
        assert result1 is True

        # 重置eval to fail for second request (would exceed stock)
        mock_redis.eval = AsyncMock(return_value=0)

        # 第二次请求90个（应该失败，只剩80）
        result2 = await service.acquire_stock_lock(sku_id="sku_123", quantity=90)
        assert result2 is False

    @pytest.mark.asyncio
    async def test_concurrent_locks_both_succeed(self):
        """测试并发锁：两个请求都成功"""
        # 第一次请求
        mock_redis = create_mock_redis_pipeline("100", "0")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)

        result1 = await service.acquire_stock_lock(sku_id="sku_123", quantity=30)
        assert result1 is True

        # 第二次请求 - also succeeds (within stock limit)
        mock_redis.eval = AsyncMock(return_value=1)

        result2 = await service.acquire_stock_lock(sku_id="sku_123", quantity=40)
        assert result2 is True


class TestTTLExpiration:
    """测试TTL过期"""

    @pytest.mark.asyncio
    async def test_lock_has_ttl(self):
        """测试锁有TTL"""
        mock_redis = create_mock_redis_pipeline("100", "0")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)
        await service.acquire_stock_lock(sku_id="sku_123", quantity=5)

        # 验证eval被调用
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_lock_ttl_value(self):
        """测试锁TTL值为300秒"""
        mock_redis = create_mock_redis_pipeline("100", "0")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)
        await service.acquire_stock_lock(sku_id="sku_123", quantity=5)

        # 验证TTL参数为300
        call_args = mock_redis.eval.call_args
        assert call_args[0][5] == 300  # ARGV[2] - TTL


class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_redis_connection_error_on_get(self):
        """测试Redis连接错误（get操作）"""
        mock_redis = create_mock_redis_pipeline(None, None)
        mock_redis.eval = AsyncMock(
            side_effect=ConnectionError("Redis connection failed")
        )

        service = StockLockService(redis_client=mock_redis)

        # 应该优雅地处理错误，返回False
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=5)
        assert result is False

    @pytest.mark.asyncio
    async def test_redis_timeout_error(self):
        """测试Redis超时错误"""
        mock_redis = create_mock_redis_pipeline(None, None)
        mock_redis.eval = AsyncMock(
            side_effect=aioredis.TimeoutError("Redis timeout")
        )

        service = StockLockService(redis_client=mock_redis)

        # 应该优雅地处理错误，返回False
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=5)
        assert result is False

    @pytest.mark.asyncio
    async def test_redis_error_on_confirm(self):
        """测试确认库存时Redis错误"""
        mock_redis = create_mock_redis_pipeline(None, None)
        mock_redis.pipeline.return_value.execute = AsyncMock(
            side_effect=ConnectionError("Redis connection failed")
        )

        service = StockLockService(redis_client=mock_redis)

        # 应该优雅地处理错误（不抛出异常）
        await service.confirm_stock(sku_id="sku_123", quantity=5)

    @pytest.mark.asyncio
    async def test_redis_error_on_release(self):
        """测试释放锁时Redis错误"""
        mock_redis = create_mock_redis_pipeline(None, None)
        mock_redis.decrby = AsyncMock(side_effect=ConnectionError("Redis connection failed"))

        service = StockLockService(redis_client=mock_redis)

        # 应该优雅地处理错误（不抛出异常）
        await service.release_stock_lock(sku_id="sku_123", quantity=5)

    @pytest.mark.asyncio
    async def test_invalid_sku_id(self):
        """测试无效的SKU ID"""
        mock_redis = create_mock_redis_pipeline("100", "0")

        service = StockLockService(redis_client=mock_redis)

        # 空字符串SKU ID
        result = await service.acquire_stock_lock(sku_id="", quantity=5)
        assert result is False


class TestStockLockServiceIntegration:
    """集成测试：完整的锁生命周期"""

    @pytest.mark.asyncio
    async def test_complete_lock_lifecycle(self):
        """测试完整的锁生命周期：获取 -> 确认 -> 释放"""
        # 步骤1：获取锁
        mock_redis = create_mock_redis_pipeline("100", "0")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)

        # 获取锁
        acquired = await service.acquire_stock_lock(sku_id="sku_123", quantity=5)
        assert acquired is True

        # 步骤2：确认库存（支付成功）
        mock_redis.decrby = AsyncMock(return_value=0)
        mock_pipeline = MagicMock()
        mock_pipeline.decrby = mock_redis.decrby
        mock_pipeline.execute = AsyncMock(return_value=[None, None])
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

        await service.confirm_stock(sku_id="sku_123", quantity=5)

        # 验证锁定和实际库存都被扣减
        assert mock_redis.decrby.call_count == 2

    @pytest.mark.asyncio
    async def test_lock_and_release_lifecycle(self):
        """测试锁获取和释放生命周期：获取 -> 释放"""
        # 步骤1：获取锁
        mock_redis = create_mock_redis_pipeline("100", "0")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)

        # 获取锁
        acquired = await service.acquire_stock_lock(sku_id="sku_123", quantity=5)
        assert acquired is True

        # 步骤2：释放锁（订单取消）
        mock_redis.decrby = AsyncMock(return_value=0)

        await service.release_stock_lock(sku_id="sku_123", quantity=5)

        # 验证只有锁定数量被减少
        mock_redis.decrby.assert_called_once_with("stock:lock:sku_123", 5)


class TestStockLockServiceEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_very_large_quantity(self):
        """测试非常大的数量"""
        mock_redis = create_mock_redis_pipeline("1000000", "0")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_123", quantity=100000)

        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_lock_different_skus(self):
        """测试不同SKU的锁"""
        # SKU1
        mock_redis = create_mock_redis_pipeline("100", "0")
        mock_redis.eval = AsyncMock(return_value=1)

        service = StockLockService(redis_client=mock_redis)

        result1 = await service.acquire_stock_lock(sku_id="sku_1", quantity=10)
        result2 = await service.acquire_stock_lock(sku_id="sku_2", quantity=5)

        assert result1 is True
        assert result2 is True

    @pytest.mark.asyncio
    async def test_stock_unlimited_not_implemented(self):
        """测试无限库存（当前实现中未实现，作为占位符）"""
        # 当前实现不支持无限库存标记
        # 如果库存为0但允许无限库存，应该返回True
        # 这个测试用于验证未来如果需要支持无限库存的情况
        mock_redis = create_mock_redis_pipeline("0", "0")
        mock_redis.eval = AsyncMock(return_value=0)

        service = StockLockService(redis_client=mock_redis)
        result = await service.acquire_stock_lock(sku_id="sku_unlimited", quantity=5)

        # 当前实现：库存为0时应该失败
        assert result is False
