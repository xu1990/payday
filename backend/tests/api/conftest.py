"""
API tests configuration - Mock problematic external dependencies

IMPORTANT: This file runs before any test imports to set up mocks
"""
import sys
from datetime import datetime
from unittest.mock import MagicMock, Mock
import pytest

# Setup mocks immediately when this file is loaded (before any test imports)
# Mock Celery
celery_mock = MagicMock()
celery_mock.shared_task = lambda **kwargs: lambda f: f
sys.modules['celery'] = celery_mock

# Mock rate limiter to prevent TypeError during app import
# This is needed because RateLimiter is not callable but used as a dependency
from unittest.mock import AsyncMock
rate_limiter_mock = MagicMock()
rate_limiter_mock.__call__ = lambda *args, **kwargs: None  # Make it callable
rate_limiter_mock.check = AsyncMock(return_value=None)  # Make check() awaitable

# Create a proper mock module that keeps real functions but mocks RateLimiter
# We need to import the real module first, then extract what we need
mock_rate_limit_module = MagicMock()
mock_rate_limit_module.RateLimiter = lambda *args, **kwargs: rate_limiter_mock
# Mock the async functions that are used
mock_rate_limit_module.get_client_identifier = AsyncMock(return_value="test_client")
mock_rate_limit_module.get_client_ip = lambda request: "127.0.0.1"
# Mock the rate limiter constants
mock_rate_limit_module.RATE_LIMIT_GENERAL = rate_limiter_mock
mock_rate_limit_module.RATE_LIMIT_LOGIN = rate_limiter_mock
mock_rate_limit_module.RATE_LIMIT_POST = rate_limiter_mock
mock_rate_limit_module.RATE_LIMIT_COMMENT = rate_limiter_mock

sys.modules['app.core.rate_limit'] = mock_rate_limit_module

# Mock tencentcloud with simple module stubs that support attribute access
class ModuleStub:
    """Simple module stub that returns itself for any attribute access"""
    def __init__(self, name=''):
        self.__name__ = name or 'tencentcloud'

    def __getattr__(self, name):
        # Return a new stub for any attribute access
        return ModuleStub(f'{self.__name__}.{name}')

    def __getitem__(self, name):
        return ModuleStub(f'{self.__name__}.{name}')

sys.modules['tencentcloud'] = ModuleStub()
# Pre-register commonly used submodules
for submodule in ['common', 'common.credential', 'common.exception', 'common.exception.tencent_cloud_sdk_exception',
                  'tms', 'tms.v20200713', 'tms.v20200713.models',
                  'ims', 'ims.v20201229', 'ims.v20201229.models',
                  'ocr', 'ocr.v20181119', 'ocr.v20181119.models']:
    sys.modules[f'tencentcloud.{submodule}'] = ModuleStub(f'tencentcloud.{submodule}')

# Mock OSS
sys.modules['oss2'] = MagicMock()

# Mock sentry_sdk
class MockSentrySdk:
    def init(self, *args, **kwargs):
        pass
    def capture_exception(self, *args, **kwargs):
        pass
    def capture_message(self, *args, **kwargs):
        pass
    def set_tag(self, *args, **kwargs):
        pass

mock_sentry = MockSentrySdk()
sys.modules['sentry_sdk'] = mock_sentry
sys.modules['sentry_sdk.integrations'] = MagicMock()
sys.modules['sentry_sdk.integrations.fastapi'] = MagicMock()
sys.modules['sentry_sdk.integrations.sqlalchemy'] = MagicMock()
sys.modules['sentry_sdk.integrations.celery'] = MagicMock()
sys.modules['sentry_sdk.integrations.redis'] = MagicMock()
sys.modules['sentry_sdk.integrations.redis'] = MagicMock()
sys.modules['sentry_sdk.integrations.argv'] = MagicMock()
sys.modules['sentry_sdk.integrations.logging'] = MagicMock()
sys.modules['sentry_sdk.integrations.excepthook'] = MagicMock()
sys.modules['sentry_sdk.integrations.dedupe'] = MagicMock()
sys.modules['sentry_sdk.integrations.httpx'] = MagicMock()

# Mock the tencent_yu service to prevent initialization issues
# This is needed because it tries to access settings attributes that don't exist
tencent_yu_mock = MagicMock()
sys.modules['app.utils.tencent_yu'] = tencent_yu_mock

# Mock the date utils module which doesn't exist
date_utils_mock = MagicMock()
date_utils_mock.now = MagicMock(return_value=datetime.now())
sys.modules['app.utils.date'] = date_utils_mock


@pytest.fixture
def client(db_session):
    """
    测试客户端 fixture - FastAPI TestClient with test database override

    这是解决 TestClient async/await 问题的关键 fixture
    它将测试数据库会话注入到 FastAPI 的依赖注入系统中
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db
    from app.core import cache as cache_module
    from unittest.mock import AsyncMock, MagicMock, patch

    # 保存原始 Redis 客户端
    original_redis = cache_module.redis_client

    # 创建一个覆盖函数，返回测试数据库会话
    # The key is that we yield db_session which is an active AsyncSession
    # The dependency system will handle calling this properly
    def override_get_db():
        yield db_session

    # 覆盖依赖
    app.dependency_overrides[get_db] = override_get_db

    # Mock CSRF manager - must be done before TestClient is created
    mock_csrf_manager = MagicMock()
    mock_csrf_manager.validate_token = AsyncMock(return_value=True)
    mock_csrf_manager.generate_token = AsyncMock(return_value="test_csrf_token")

    try:
        # Mock Redis for tests
        mock_redis_client = MagicMock()
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis_client.set = AsyncMock(return_value=True)
        mock_redis_client.setex = AsyncMock(return_value=True)
        mock_redis_client.delete = AsyncMock(return_value=True)
        mock_redis_client.incr = AsyncMock(return_value=1)
        mock_redis_client.decr = AsyncMock(return_value=0)
        mock_redis_client.zadd = AsyncMock(return_value=1)
        mock_redis_client.zrevrange = AsyncMock(return_value=[])
        mock_redis_client.exists = AsyncMock(return_value=0)
        mock_redis_client.zrem = AsyncMock(return_value=1)
        mock_redis_client.close = AsyncMock(return_value=None)  # Mock close method
        cache_module.redis_client = mock_redis_client

        # Mock CSRF validation - patch at the module level where it's imported
        with patch('app.core.deps.csrf_manager', mock_csrf_manager):
            # 使用 TestClient，它在同步上下文中运行
            with TestClient(app) as test_client:
                yield test_client
    finally:
        # 清理依赖覆盖
        app.dependency_overrides.clear()
        # 恢复原始 Redis 客户端
        cache_module.redis_client = original_redis
