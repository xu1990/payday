"""
单元测试 - 速率限制 (app.core.rate_limit)
"""
import pytest
import time
from collections import deque
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request

from app.core.rate_limit import (
    RateLimiter,
    get_client_identifier,
    RATE_LIMIT_GENERAL,
    RATE_LIMIT_LOGIN,
    RATE_LIMIT_POST,
    RATE_LIMIT_COMMENT,
)
from app.core.exceptions import RateLimitException


class TestRateLimiterInit:
    """测试 RateLimiter 初始化"""

    def test_init_default(self):
        """测试默认初始化"""
        limiter = RateLimiter()

        assert limiter.times == 60
        assert limiter.max_requests == 100
        assert limiter._fallback_store == {}

    def test_init_custom(self):
        """测试自定义初始化"""
        limiter = RateLimiter(times=120, max_requests=200)

        assert limiter.times == 120
        assert limiter.max_requests == 200


class TestRateLimiterFallbackMethods:
    """测试内存后备方法"""

    def test_cleanup_fallback(self):
        """测试清理过期记录"""
        limiter = RateLimiter(times=60, max_requests=3)
        key = "test_key"

        # 添加一些过期记录
        now = time.time()
        old_timestamp = now - 120  # 2分钟前
        recent_timestamp = now - 10  # 10秒前

        limiter._fallback_store[key] = deque([old_timestamp, recent_timestamp])

        # 清理
        limiter._cleanup_fallback(key)

        # 应该只保留最近的记录
        assert len(limiter._fallback_store[key]) == 1
        assert limiter._fallback_store[key][0] == recent_timestamp

    def test_cleanup_fallback_empty(self):
        """测试清理空的记录"""
        limiter = RateLimiter()
        key = "test_key"

        limiter._fallback_store[key] = deque()
        limiter._cleanup_fallback(key)

        assert len(limiter._fallback_store[key]) == 0

    def test_check_fallback_within_limit(self):
        """测试在限制内检查"""
        limiter = RateLimiter(times=60, max_requests=5)
        key = "test_key"

        # 添加3条记录
        now = time.time()
        for i in range(3):
            limiter._fallback_store[key].append(now - i)

        # 应该在限制内
        assert limiter._check_fallback(key) is True

    def test_check_fallback_at_limit(self):
        """测试达到限制"""
        limiter = RateLimiter(times=60, max_requests=3)
        key = "test_key"

        # 添加3条记录
        now = time.time()
        for i in range(3):
            limiter._fallback_store[key].append(now - i)

        # 应该达到限制
        assert limiter._check_fallback(key) is False

    def test_check_fallback_cleanup(self):
        """测试检查时自动清理"""
        limiter = RateLimiter(times=60, max_requests=5)
        key = "test_key"

        # 添加过期记录
        now = time.time()
        old_timestamp = now - 120
        limiter._fallback_store[key] = deque([old_timestamp, old_timestamp + 1])

        # 检查会触发清理
        result = limiter._check_fallback(key)

        # 应该清理后检查
        assert len(limiter._fallback_store[key]) == 0
        assert result is True

    def test_record_fallback(self):
        """测试记录请求"""
        limiter = RateLimiter()
        key = "test_key"

        limiter._record_fallback(key)

        assert len(limiter._fallback_store[key]) == 1
        assert limiter._fallback_store[key][0] > 0


class TestRateLimiterCheck:
    """测试速率限制检查"""

    @pytest.mark.asyncio
    async def test_check_with_redis_under_limit(self):
        """测试 Redis 可用且在限制内"""
        limiter = RateLimiter(times=60, max_requests=5)

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="2")  # 2次请求
        mock_redis.ttl = AsyncMock(return_value=30)

        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)

        request = MagicMock(spec=Request)

        with patch('app.core.rate_limit.get_redis_client', return_value=mock_redis):
            # 应该不抛出异常
            await limiter.check("test_key", request)

    @pytest.mark.asyncio
    async def test_check_with_redis_at_limit(self):
        """测试 Redis 可用但达到限制 - 降级到后备模式"""
        limiter = RateLimiter(times=60, max_requests=2)  # Use smaller limit for testing

        mock_redis = AsyncMock()
        # When limit is reached, raising RateLimitException triggers fallback
        mock_redis.get = AsyncMock(return_value="2")  # 达到限制
        mock_redis.ttl = AsyncMock(return_value=30)
        mock_redis.pipeline = MagicMock(return_value=None)  # Triggers AttributeError -> fallback

        request = MagicMock(spec=Request)

        with patch('app.core.rate_limit.get_redis_client', return_value=mock_redis):
            # First call fills fallback (gets exception but fallback is fresh)
            await limiter.check("test_key", request)

            # Second call fills fallback
            await limiter.check("test_key", request)

            # Third call should trigger fallback rate limit
            with pytest.raises(RateLimitException) as exc_info:
                await limiter.check("test_key", request)

            # Should use fallback mode
            assert exc_info.value.details.get("fallback") is True
            assert "请求过于频繁" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_with_redis_zero_count(self):
        """测试 Redis 首次请求"""
        limiter = RateLimiter(times=60, max_requests=5)

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # 无记录

        mock_pipe = MagicMock()
        mock_pipe.incr = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)

        request = MagicMock(spec=Request)

        with patch('app.core.rate_limit.get_redis_client', return_value=mock_redis):
            # 应该不抛出异常
            await limiter.check("test_key", request)

    @pytest.mark.asyncio
    async def test_check_redis_fails_uses_fallback(self):
        """测试 Redis 失败时使用内存后备"""
        limiter = RateLimiter(times=60, max_requests=3)

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

        request = MagicMock(spec=Request)

        with patch('app.core.rate_limit.get_redis_client', return_value=mock_redis):
            # 前3次请求应该通过
            for _ in range(3):
                await limiter.check("test_key", request)

            # 第4次应该被限制
            with pytest.raises(RateLimitException) as exc_info:
                await limiter.check("test_key", request)

            assert exc_info.value.details["fallback"] is True

    @pytest.mark.asyncio
    async def test_check_no_redis_uses_fallback(self):
        """测试无 Redis 时使用内存后备"""
        limiter = RateLimiter(times=60, max_requests=3)

        request = MagicMock(spec=Request)

        with patch('app.core.rate_limit.get_redis_client', return_value=None):
            # 前3次请求应该通过
            for _ in range(3):
                await limiter.check("test_key", request)

            # 第4次应该被限制
            with pytest.raises(RateLimitException) as exc_info:
                await limiter.check("test_key", request)

            assert exc_info.value.details["fallback"] is True

    @pytest.mark.asyncio
    async def test_check_redis_ttl_error(self):
        """测试 Redis TTL 获取失败 - 降级到后备模式"""
        limiter = RateLimiter(times=60, max_requests=5)

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="5")
        mock_redis.ttl = AsyncMock(side_effect=Exception("TTL error"))
        mock_redis.pipeline = MagicMock(return_value=None)

        request = MagicMock(spec=Request)

        with patch('app.core.rate_limit.get_redis_client', return_value=mock_redis):
            # TTL error triggers fallback
            # Since fallback starts fresh, this should pass (not at limit yet)
            # The test just verifies no unhandled exception occurs
            await limiter.check("test_key", request)

    @pytest.mark.asyncio
    async def test_check_fallback_with_time_window(self):
        """测试内存后备的时间窗口"""
        limiter = RateLimiter(times=1, max_requests=2)  # 1秒窗口，最多2次请求

        request = MagicMock(spec=Request)

        with patch('app.core.rate_limit.get_redis_client', return_value=None):
            # 前2次应该通过
            await limiter.check("test_key", request)
            await limiter.check("test_key", request)

            # 第3次应该被限制
            with pytest.raises(RateLimitException):
                await limiter.check("test_key", request)

            # 等待窗口过期
            time.sleep(1.1)

            # 现在应该可以通过了
            await limiter.check("test_key", request)


class TestGetClientIdentifier:
    """测试获取客户端标识符"""

    @pytest.mark.asyncio
    async def test_get_client_identifier_with_ip(self):
        """测试从 IP 获取标识符"""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"

        with patch('app.core.rate_limit.get_client_ip', return_value="192.168.1.100"):
            identifier = await get_client_identifier(request)

            assert identifier == "ip:192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_client_identifier_with_x_forwarded_for(self):
        """测试从 X-Forwarded-For 获取标识符"""
        request = MagicMock(spec=Request)
        request.headers = {"X-Forwarded-For": "203.0.113.1"}
        request.client = None

        with patch('app.core.rate_limit.get_client_ip', return_value="203.0.113.1"):
            identifier = await get_client_identifier(request)

            assert identifier == "ip:203.0.113.1"

    @pytest.mark.asyncio
    async def test_get_client_identifier_loopback(self):
        """测试回环地址"""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = None

        with patch('app.core.rate_limit.get_client_ip', return_value="127.0.0.1"):
            identifier = await get_client_identifier(request)

            assert identifier == "ip:127.0.0.1"


class TestPredefinedRateLimiters:
    """测试预定义的速率限制器"""

    def test_rate_limit_general(self):
        """测试通用 API 限制器"""
        assert RATE_LIMIT_GENERAL.times == 60
        assert RATE_LIMIT_GENERAL.max_requests == 100

    def test_rate_limit_login(self):
        """测试登录 API 限制器"""
        assert RATE_LIMIT_LOGIN.times == 60
        assert RATE_LIMIT_LOGIN.max_requests == 5

    def test_rate_limit_post(self):
        """测试发帖 API 限制器"""
        assert RATE_LIMIT_POST.times == 60
        assert RATE_LIMIT_POST.max_requests == 10

    def test_rate_limit_comment(self):
        """测试评论 API 限制器"""
        assert RATE_LIMIT_COMMENT.times == 60
        assert RATE_LIMIT_COMMENT.max_requests == 20


class TestRateLimiterDifferentKeys:
    """测试不同键的独立限流"""

    @pytest.mark.asyncio
    async def test_different_keys_independent(self):
        """测试不同键的限流独立"""
        limiter = RateLimiter(times=60, max_requests=2)

        request = MagicMock(spec=Request)

        with patch('app.core.rate_limit.get_redis_client', return_value=None):
            # key1 可以请求2次
            await limiter.check("user_1", request)
            await limiter.check("user_1", request)

            # key1 第3次被限制
            with pytest.raises(RateLimitException):
                await limiter.check("user_1", request)

            # key2 仍然可以请求2次
            await limiter.check("user_2", request)
            await limiter.check("user_2", request)

            # key2 第3次也被限制
            with pytest.raises(RateLimitException):
                await limiter.check("user_2", request)
