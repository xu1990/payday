"""
API tests configuration - Mock problematic external dependencies

IMPORTANT: This file runs before any test imports to set up mocks
"""
import sys
from datetime import datetime
from unittest.mock import MagicMock, Mock
import pytest

# Store the original modules before mocking
_original_modules = {}

# Setup mocks immediately when this file is loaded (before any test imports)
# Mock Celery for API tests (this is loaded by tests/api/ only)
celery_mock = MagicMock()
celery_mock.shared_task = lambda **kwargs: lambda f: f
_original_modules['celery'] = sys.modules.get('celery')
sys.modules['celery'] = celery_mock

# Note: Removed app.core.rate_limit mock to avoid breaking test_rate_limit.py
# API tests don't use rate_limit directly

# Mock OSS
_original_modules['oss2'] = sys.modules.get('oss2')
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
_sentry_modules = ['sentry_sdk', 'sentry_sdk.integrations', 'sentry_sdk.integrations.fastapi',
    'sentry_sdk.integrations.sqlalchemy', 'sentry_sdk.integrations.celery', 'sentry_sdk.integrations.redis',
    'sentry_sdk.integrations.argv', 'sentry_sdk.integrations.logging', 'sentry_sdk.integrations.excepthook',
    'sentry_sdk.integrations.dedupe', 'sentry_sdk.integrations.httpx']

for mod in _sentry_modules:
    _original_modules[mod] = sys.modules.get(mod)
    sys.modules[mod] = MagicMock() if not mod.endswith('integrations') else MagicMock()

# Note: Removed global mocks for app.utils.tencent_yu and app.utils.date
# These were causing test pollution for test_tencent_yu.py
# API tests should patch these locally if needed


@pytest.fixture(scope="session", autouse=True)
def cleanup_api_mocks():
    """Clean up mocks after all api tests are done"""
    yield
    # Restore original modules
    for mod_name, original_module in _original_modules.items():
        if original_module is None:
            sys.modules.pop(mod_name, None)
        else:
            sys.modules[mod_name] = original_module


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
            # Mock background tasks to prevent async_session_maker issues
            # Patch at the import location in post.py
            with patch('app.api.v1.post.run_risk_check_for_post', return_value=None):
                # 使用 TestClient，它在同步上下文中运行
                with TestClient(app) as test_client:
                    yield test_client
    finally:
        # 清理依赖覆盖
        app.dependency_overrides.clear()
        # 恢复原始 Redis 客户端
        cache_module.redis_client = original_redis
