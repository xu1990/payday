"""
单元测试 - Prometheus 监控指标 (app.utils.metrics)
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response

from app.utils import metrics


class TestMetricsInitialization:
    """测试指标初始化"""

    def test_registry_exists(self):
        """测试 registry 存在"""
        assert metrics.registry is not None

    def test_http_metrics_exist(self):
        """测试 HTTP 指标存在"""
        assert metrics.http_requests_total is not None
        assert metrics.http_request_duration_seconds is not None
        assert metrics.http_requests_in_progress is not None

    def test_business_metrics_exist(self):
        """测试业务指标存在"""
        assert metrics.users_total is not None
        assert metrics.users_active is not None
        assert metrics.posts_total is not None
        assert metrics.posts_created_total is not None
        assert metrics.comments_total is not None
        assert metrics.comments_created_total is not None
        assert metrics.likes_total is not None

    def test_cache_metrics_exist(self):
        """测试缓存指标存在"""
        assert metrics.cache_hits_total is not None
        assert metrics.cache_misses_total is not None
        assert metrics.cache_operations_total is not None

    def test_risk_metrics_exist(self):
        """测试风控指标存在"""
        assert metrics.risk_checks_total is not None
        assert metrics.risk_check_duration_seconds is not None

    def test_celery_metrics_exist(self):
        """测试 Celery 指标存在"""
        assert metrics.celery_tasks_total is not None
        assert metrics.celery_task_duration_seconds is not None
        assert metrics.celery_queue_length is not None

    def test_app_info_exists(self):
        """测试应用信息存在"""
        assert metrics.app_info is not None


class TestTrackRequestTime:
    """测试 track_request_time 装饰器"""

    @pytest.mark.asyncio
    async def test_track_async_function(self):
        """测试跟踪异步函数"""
        @metrics.track_request_time
        async def test_function():
            await asyncio.sleep(0.01)
            return "result"

        result = await test_function()

        assert result == "result"

    @pytest.mark.asyncio
    async def test_track_sync_function(self):
        """测试跟踪同步函数"""
        @metrics.track_request_time
        def test_function():
            return "sync_result"

        result = test_function()

        assert result == "sync_result"

    @pytest.mark.asyncio
    async def test_track_async_function_with_exception(self):
        """测试异步函数抛出异常"""
        @metrics.track_request_time
        async def test_function():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await test_function()

    @pytest.mark.asyncio
    async def test_track_sync_function_with_exception(self):
        """测试同步函数抛出异常"""
        @metrics.track_request_time
        def test_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_function()


class TestPrometheusMiddleware:
    """测试 Prometheus 中间件"""

    @pytest.mark.asyncio
    async def test_skip_metrics_endpoint(self):
        """测试跳过 /metrics 端点"""
        middleware = metrics.PrometheusMiddleware(MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = '/metrics'
        mock_request.method = 'GET'

        mock_call_next = AsyncMock(return_value=MagicMock(spec=Response, status_code=200))

        await middleware.dispatch(mock_request, mock_call_next)

        # Should call next without tracking
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_skip_health_check_endpoints(self):
        """测试跳过健康检查端点"""
        middleware = metrics.PrometheusMiddleware(MagicMock())

        for path in ['/health', '/readiness', '/liveness']:
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = path
            mock_request.method = 'GET'

            mock_call_next = AsyncMock(return_value=MagicMock(spec=Response, status_code=200))

            await middleware.dispatch(mock_request, mock_call_next)

            # Should call next without tracking
            mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_track_normal_request(self):
        """测试跟踪普通请求"""
        middleware = metrics.PrometheusMiddleware(MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = '/api/v1/posts'
        mock_request.method = 'GET'

        mock_response = MagicMock(spec=Response, status_code=200)
        mock_call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_track_request_with_error(self):
        """测试请求发生错误"""
        middleware = metrics.PrometheusMiddleware(MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = '/api/v1/posts'
        mock_request.method = 'GET'

        # Simulate error in call_next
        mock_call_next = AsyncMock(side_effect=Exception("Test error"))

        with pytest.raises(Exception, match="Test error"):
            await middleware.dispatch(mock_request, mock_call_next)


class TestGetDbPoolMetrics:
    """测试获取数据库连接池指标"""

    @pytest.mark.asyncio
    async def test_get_db_pool_metrics_success(self):
        """测试成功获取连接池指标"""
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.overflow.return_value = 0
        mock_pool.checkedout.return_value = 5

        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        # Patch at the import location inside get_db_pool_metrics
        with patch('app.core.database._get_async_engine', return_value=mock_engine):
            await metrics.get_db_pool_metrics()

            # Verify metrics were set (no exception means success)
            mock_pool.size.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_pool_metrics_failure(self):
        """测试获取连接池指标失败"""
        with patch('app.core.database._get_async_engine', side_effect=Exception("DB error")):
            # Should not raise exception, just log warning
            await metrics.get_db_pool_metrics()


class TestCollectApplicationMetrics:
    """测试收集应用级指标"""

    @pytest.mark.asyncio
    async def test_collect_application_metrics_success(self):
        """测试成功收集应用指标"""
        with patch('app.utils.metrics.get_db_pool_metrics', new_callable=AsyncMock):
            await metrics.collect_application_metrics()

    @pytest.mark.asyncio
    async def test_collect_application_metrics_failure(self):
        """测试收集应用指标失败"""
        with patch('app.utils.metrics.get_db_pool_metrics', new_callable=AsyncMock, side_effect=Exception("Collect error")):
            # Should not raise exception, just log warning
            await metrics.collect_application_metrics()


class TestGetMetricsText:
    """测试获取指标文本"""

    def test_get_metrics_text(self):
        """测试获取 Prometheus 文本格式指标"""
        result = metrics.get_metrics_text()

        assert isinstance(result, bytes)
        assert len(result) > 0


class TestGetMetricsContentType:
    """测试获取指标内容类型"""

    def test_get_metrics_content_type(self):
        """测试获取 content type"""
        result = metrics.get_metrics_content_type()

        assert result == 'text/plain; version=0.0.4; charset=utf-8'


class TestHelperFunctions:
    """测试辅助函数"""

    def test_inc_cache_hits(self):
        """测试增加缓存命中"""
        metrics.inc_cache_hits('user')
        metrics.inc_cache_hits('post')

    def test_inc_cache_misses(self):
        """测试增加缓存未命中"""
        metrics.inc_cache_misses('user')
        metrics.inc_cache_misses('post')

    def test_inc_cache_operations(self):
        """测试增加缓存操作"""
        metrics.inc_cache_operations('user', 'get')
        metrics.inc_cache_operations('user', 'set')
        metrics.inc_cache_operations('post', 'delete')

    def test_inc_posts_created(self):
        """测试增加创建帖子计数"""
        metrics.inc_posts_created()
        metrics.inc_posts_created()

    def test_inc_comments_created(self):
        """测试增加创建评论计数"""
        metrics.inc_comments_created()
        metrics.inc_comments_created()

    def test_inc_risk_checks(self):
        """测试增加风控检查计数"""
        metrics.inc_risk_checks('post', 'approve')
        metrics.inc_risk_checks('comment', 'reject')
        metrics.inc_risk_checks('post', 'manual')

    def test_observe_risk_check_duration(self):
        """测试记录风控检查耗时"""
        metrics.observe_risk_check_duration('text', 0.5)
        metrics.observe_risk_check_duration('image', 1.2)
        metrics.observe_risk_check_duration('ocr', 0.8)

    def test_set_app_info(self):
        """测试设置应用信息"""
        metrics.set_app_info('1.0.0', '2024-01-01')

    def test_set_app_info_with_git_commit(self):
        """测试设置应用信息（含 git commit）"""
        metrics.set_app_info('1.0.0', '2024-01-01', 'abc123')
