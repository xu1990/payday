"""
Pytest 配置和共享 fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.base import Base
from app.models.user import User
from app.models.post import Post
from app.models.salary import SalaryRecord
from app.models.payday import PaydayConfig
from app.models.membership import Membership, MembershipOrder, AppTheme
from app.models.notification import Notification
from tests.test_utils import TestDataFactory


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

    session = async_session_maker()
    try:
        yield session
    finally:
        # 清理
        await session.close()
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


# Fixtures for authenticated requests
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    return await TestDataFactory.create_user(db_session)


@pytest.fixture
async def test_admin(db_session: AsyncSession):
    """创建测试管理员用户"""
    from app.models.admin import AdminUser
    from app.core.security import hash_password

    admin = AdminUser(
        username="test_admin",
        password_hash=hash_password("test_password"),
        role="admin",
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
def user_token(test_user: User) -> str:
    """生成用户JWT token"""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def admin_token(test_admin) -> str:
    """生成管理员JWT token"""
    return create_access_token(
        data={"sub": str(test_admin.id), "scope": "admin"}
    )


@pytest.fixture
def user_headers(user_token: str) -> dict:
    """用户认证请求头"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """管理员认证请求头"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
async def async_client(db_session: AsyncSession):
    """异步HTTP客户端用于集成测试，使用测试数据库会话"""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from unittest.mock import patch
    from app.core.database import get_db

    # Override the get_db dependency to use our test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


# External service mock fixtures
@pytest.fixture
def mock_wechat_auth():
    """Mock微信认证API"""
    with patch('app.services.auth_service.wechat_code2session', new_callable=AsyncMock) as mock:
        mock.return_value = {
            "openid": "test_openid",
            "session_key": "test_session_key"
        }
        yield mock


@pytest.fixture
def mock_wechat_pay():
    """Mock微信支付API"""
    async def mock_create_payment(**kwargs):
        """Mock that returns the actual out_trade_no that was passed in"""
        return {
            "timeStamp": "1234567890",
            "nonceStr": "test_nonce",
            "package": "prepay_id=test",
            "signType": "MD5",
            "paySign": "test_sign",
            "out_trade_no": kwargs.get("out_trade_no", "test_order_id"),
        }

    mock = AsyncMock(side_effect=mock_create_payment)
    # Patch at the import location in payment_service
    with patch('app.services.payment_service.create_mini_program_payment', mock):
        yield mock


@pytest.fixture
def mock_yu_moderation():
    """Mock腾讯云天御内容审核"""
    with patch('app.services.risk_service.yu_client') as mock:
        mock.text_moderation = AsyncMock(return_value={
            "Pass": True,
            "Score": 0,
            "Label": ""
        })
        mock.image_moderation = AsyncMock(return_value={
            "Pass": True,
            "Score": 0,
            "Label": ""
        })
        yield mock


@pytest.fixture
def mock_cos_upload():
    """Mock腾讯云COS上传"""
    with patch('app.services.storage_service.cos_client') as mock:
        mock.upload_file = AsyncMock(return_value={
            "url": "https://test.cos.ap-guangzhou.myqcloud.com/test.jpg",
            "path": "test.jpg"
        })
        yield mock


# Data fixtures
@pytest.fixture
async def test_post(db_session: AsyncSession, test_user: User) -> Post:
    """创建测试帖子"""
    return await TestDataFactory.create_post(db_session, test_user.id)


@pytest.fixture
async def test_salary(db_session: AsyncSession, test_user: User) -> SalaryRecord:
    """创建测试薪资记录"""
    # First create a payday config for the salary
    from app.models.payday import PaydayConfig
    config = PaydayConfig(
        user_id=test_user.id,
        job_name="测试工作",
        payday=25,
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    return await TestDataFactory.create_salary(db_session, test_user.id, config.id)


@pytest.fixture
async def test_membership(db_session: AsyncSession) -> Membership:
    """创建测试会员套餐"""
    return await TestDataFactory.create_membership(db_session)


@pytest.fixture
async def test_order(
    db_session: AsyncSession,
    test_user: User,
    test_membership: Membership
) -> MembershipOrder:
    """创建测试订单"""
    return await TestDataFactory.create_order(
        db_session,
        test_user.id,
        test_membership.id
    )


@pytest.fixture
async def test_comment(db_session: AsyncSession, test_user: User, test_post: Post):
    """创建测试评论"""
    return await TestDataFactory.create_comment(
        db_session,
        test_user.id,
        test_post.id,
    )


@pytest.fixture
async def test_theme(db_session: AsyncSession) -> AppTheme:
    """创建测试主题"""
    return await TestDataFactory.create_theme(db_session)


@pytest.fixture
async def test_payday_config(db_session: AsyncSession, test_user: User) -> PaydayConfig:
    """创建测试发薪日配置"""
    return await TestDataFactory.create_payday_config(db_session, test_user.id)


@pytest.fixture
async def test_notification(db_session: AsyncSession, test_user: User) -> Notification:
    """创建测试通知"""
    return await TestDataFactory.create_notification(db_session, test_user.id)
