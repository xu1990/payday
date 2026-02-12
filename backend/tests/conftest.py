"""
Pytest 配置和共享 fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.base import Base


# 测试数据库 URL（使用内存数据库或测试数据库）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    创建测试数据库会话

    每个测试函数都会创建一个新的内存数据库
    """
    # 创建测试引擎
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建会话
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def mock_settings():
    """Mock 配置"""
    settings = get_settings()
    # 覆盖测试需要的配置
    settings.debug = True
    settings.database_url = TEST_DATABASE_URL
    return settings


@pytest.fixture
def mock_redis():
    """Mock Redis"""
    from unittest.mock import AsyncMock, MagicMock

    # 创建 mock Redis 客户端
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.setex = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.decr = AsyncMock(return_value=0)
    mock_redis.zadd = AsyncMock(return_value=1)
    mock_redis.zrevrange = AsyncMock(return_value=[])
    mock_redis.exists = AsyncMock(return_value=0)

    return mock_redis


@pytest.fixture
def mock_cache_service(mock_redis):
    """Mock 缓存服务"""
    from unittest.mock import patch

    with patch('app.services.cache_service.redis', mock_redis):
        yield
