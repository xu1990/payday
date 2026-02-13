"""
单元测试 - Redis 缓存服务模块 (app.core.cache)
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from app.core.cache import (
    get_redis_client,
    close_redis,
    get_user_info_key,
    get_payday_status_key,
    get_post_hot_key,
    get_post_view_key,
    get_like_status_key,
    PostCacheService,
    LikeCacheService,
    USER_INFO_TTL,
    PAYDAY_STATUS_TTL,
    POST_HOT_TTL,
    POST_VIEW_TTL,
    LIKE_STATUS_TTL,
)


class TestCacheKeyFunctions:
    """测试缓存键生成函数"""

    def test_get_user_info_key(self):
        """测试用户信息缓存键"""
        key = get_user_info_key("user_123")
        assert key == "user:info:user_123"

    def test_get_payday_status_key(self):
        """测试发薪日状态缓存键"""
        key = get_payday_status_key("user_456", "2024-01-15")
        assert key == "payday:status:user_456:2024-01-15"

    def test_get_post_hot_key(self):
        """测试热门帖子缓存键"""
        key = get_post_hot_key("2024-01-15")
        assert key == "post:hot:2024-01-15"

    def test_get_post_view_key(self):
        """测试帖子浏览量缓存键"""
        key = get_post_view_key("post_789")
        assert key == "post:view:post_789"

    def test_get_like_status_key(self):
        """测试点赞状态缓存键"""
        key = get_like_status_key("user_123", "post", "post_456")
        assert key == "like:status:user_123:post:post_456"


class TestRedisClient:
    """测试Redis客户端管理"""

    @pytest.mark.asyncio
    async def test_get_redis_client_first_call(self):
        """测试首次获取Redis客户端"""
        mock_redis_instance = MagicMock()
        mock_from_url = AsyncMock(return_value=mock_redis_instance)

        with patch('app.core.cache.aioredis.from_url', mock_from_url) as mock_func:
            with patch('app.core.cache.redis_client', None):
                mock_func.return_value = mock_redis_instance
                result = await get_redis_client()
                assert result == mock_redis_instance

    @pytest.mark.asyncio
    async def test_get_redis_client_cached(self):
        """测试获取缓存的Redis客户端"""
        mock_cached_client = MagicMock()

        with patch('app.core.cache.redis_client', mock_cached_client):
            result = await get_redis_client()
            assert result == mock_cached_client

    @pytest.mark.asyncio
    async def test_close_redis(self):
        """测试关闭Redis连接"""
        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()

        with patch('app.core.cache.redis_client', mock_redis):
            await close_redis()
            mock_redis.close.assert_called_once()

        # 验证客户端被设置为None
        with patch('app.core.cache.redis_client', None):
            # 再次关闭不应该出错
            await close_redis()


class TestPostCacheService:
    """测试帖子缓存服务"""

    @pytest.mark.asyncio
    async def test_add_to_hot_posts_default_date(self):
        """测试添加帖子到热门列表 - 默认日期"""
        mock_redis = AsyncMock()
        mock_redis.zadd = AsyncMock()
        mock_redis.expire = AsyncMock()

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            await PostCacheService.add_to_hot_posts("post_123", 100.5)

            # 验证调用
            mock_redis.zadd.assert_called_once()
            mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_to_hot_posts_custom_date(self):
        """测试添加帖子到热门列表 - 自定义日期"""
        mock_redis = AsyncMock()
        mock_redis.zadd = AsyncMock()
        mock_redis.expire = AsyncMock()

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            await PostCacheService.add_to_hot_posts("post_456", 95.0, date="2024-01-15")

            # 验证调用
            mock_redis.zadd.assert_called_once()
            mock_redis.expire.assert_called_once_with("post:hot:2024-01-15", POST_HOT_TTL)

    @pytest.mark.asyncio
    async def test_get_hot_posts_default_date(self):
        """测试获取热门帖子 - 默认日期"""
        mock_redis = AsyncMock()
        mock_redis.zrevrange = AsyncMock(return_value=["post_1", "post_2", "post_3"])

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            result = await PostCacheService.get_hot_posts()
            assert result == ["post_1", "post_2", "post_3"]
            mock_redis.zrevrange.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_hot_posts_custom_range(self):
        """测试获取热门帖子 - 自定义范围"""
        mock_redis = AsyncMock()
        mock_redis.zrevrange = AsyncMock(return_value=["post_1", "post_2"])

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            result = await PostCacheService.get_hot_posts(date="2024-01-15", start=0, end=10)
            assert result == ["post_1", "post_2"]
            mock_redis.zrevrange.assert_called_once_with("post:hot:2024-01-15", 0, 10)

    @pytest.mark.asyncio
    async def test_remove_from_hot_posts(self):
        """测试从热门列表移除帖子"""
        mock_redis = AsyncMock()
        mock_redis.zrem = AsyncMock()

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            await PostCacheService.remove_from_hot_posts("post_123", date="2024-01-15")
            mock_redis.zrem.assert_called_once_with("post:hot:2024-01-15", "post_123")

    @pytest.mark.asyncio
    async def test_increment_view_count(self):
        """测试增加帖子浏览量"""
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=42)
        mock_redis.expire = AsyncMock()

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            result = await PostCacheService.increment_view_count("post_123")
            assert result == 42
            mock_redis.incr.assert_called_once_with("post:view:post_123")
            mock_redis.expire.assert_called_once_with("post:view:post_123", POST_VIEW_TTL)

    @pytest.mark.asyncio
    async def test_get_view_count_exists(self):
        """测试获取帖子浏览量 - 存在"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="100")

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            result = await PostCacheService.get_view_count("post_123")
            assert result == 100
            mock_redis.get.assert_called_once_with("post:view:post_123")

    @pytest.mark.asyncio
    async def test_get_view_count_not_exists(self):
        """测试获取帖子浏览量 - 不存在"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            result = await PostCacheService.get_view_count("post_123")
            assert result == 0


class TestLikeCacheService:
    """测试点赞缓存服务"""

    @pytest.mark.asyncio
    async def test_set_like_status(self):
        """测试设置点赞状态"""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            await LikeCacheService.set_like_status("user_123", "post", "post_456")
            mock_redis.set.assert_called_once_with(
                "like:status:user_123:post:post_456",
                "1",
                ex=LIKE_STATUS_TTL
            )

    @pytest.mark.asyncio
    async def test_remove_like_status(self):
        """测试移除点赞状态"""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            await LikeCacheService.remove_like_status("user_123", "post", "post_456")
            mock_redis.delete.assert_called_once_with("like:status:user_123:post:post_456")

    @pytest.mark.asyncio
    async def test_is_liked_true(self):
        """测试检查是否已点赞 - 已点赞"""
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=1)

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            result = await LikeCacheService.is_liked("user_123", "post", "post_456")
            assert result is True
            mock_redis.exists.assert_called_once_with("like:status:user_123:post:post_456")

    @pytest.mark.asyncio
    async def test_is_liked_false(self):
        """测试检查是否已点赞 - 未点赞"""
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=0)

        with patch('app.core.cache.get_redis_client', return_value=mock_redis):
            result = await LikeCacheService.is_liked("user_123", "post", "post_456")
            assert result is False


class TestCacheTTLConstants:
    """测试缓存TTL常量"""

    def test_ttl_constants(self):
        """测试TTL常量值"""
        assert USER_INFO_TTL == 3600
        assert PAYDAY_STATUS_TTL == 86400
        assert POST_HOT_TTL == 86400
        assert POST_VIEW_TTL == 604800
        assert LIKE_STATUS_TTL == 604800
