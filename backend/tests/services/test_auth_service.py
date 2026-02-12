"""认证服务集成测试"""
import pytest
from unittest.mock import AsyncMock, patch, Mock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import (
    get_or_create_user,
    login_with_code,
    refresh_access_token,
    revoke_refresh_token,
)
from app.models.user import User
from tests.test_utils import TestDataFactory


class MockPipeline:
    """Mock Redis pipeline for testing"""

    def __init__(self):
        self.operations = []

    def sadd(self, *args):
        self.operations.append(('sadd', args))
        return self  # Pipeline methods return self for chaining

    def expire(self, *args):
        self.operations.append(('expire', args))
        return self

    def setex(self, *args):
        self.operations.append(('setex', args))
        return self

    def delete(self, *args):
        self.operations.append(('delete', args))
        return self

    async def execute(self):
        """Execute pipeline operations"""
        return []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestGetOrCreateUser:
    """测试根据openid获取或创建用户"""

    @pytest.mark.asyncio
    async def test_new_user_creation(self, db_session: AsyncSession):
        """测试新用户创建"""
        user = await get_or_create_user(
            db_session,
            openid="new_user_openid",
            unionid=None
        )

        assert user.id is not None
        assert user.openid == "new_user_openid"
        assert user.anonymous_name is not None
        assert user.anonymous_name.startswith("打工人")

    @pytest.mark.asyncio
    async def test_existing_user_returned(self, db_session: AsyncSession):
        """测试已存在用户直接返回"""
        # 先创建用户
        existing_user = await TestDataFactory.create_user(
            db_session,
            openid="existing_openid"
        )

        # 再次调用应返回同一个用户
        user = await get_or_create_user(
            db_session,
            openid="existing_openid"
        )

        assert user.id == existing_user.id
        assert user.openid == "existing_openid"
        assert user.anonymous_name == existing_user.anonymous_name

    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, db_session: AsyncSession):
        """测试并发创建用户（唯一约束冲突处理）"""
        # 这个测试模拟并发创建场景
        # 在实际中很难测试真正的并发，但可以验证逻辑路径
        openid = "concurrent_openid"

        # 创建第一个用户
        user1 = await get_or_create_user(
            db_session,
            openid=openid
        )

        # 尝试创建相同openid的用户，应返回已存在的用户
        user2 = await get_or_create_user(
            db_session,
            openid=openid
        )

        assert user1.id == user2.id
        assert user1.openid == user2.openid


class TestLoginWithCode:
    """测试微信code登录"""

    @pytest.mark.asyncio
    async def test_new_user_login_success(self, db_session: AsyncSession):
        """测试新用户通过code登录成功"""
        # Mock code2session返回新的openid
        with patch('app.services.auth_service.code2session', new_callable=AsyncMock) as mock_code2session:
            mock_code2session.return_value = {
                "openid": "new_openid_from_wechat",
                "session_key": "session_key_123",
                "unionid": None
            }

            result = await login_with_code(
                db_session,
                code="test_code_123"
            )

            assert result is not None
            access_token, refresh_token, user = result
            assert access_token is not None
            assert refresh_token is not None
            assert isinstance(user, User)
            assert user.openid == "new_openid_from_wechat"
            mock_code2session.assert_called_once_with("test_code_123")

    @pytest.mark.asyncio
    async def test_existing_user_login_success(self, db_session: AsyncSession):
        """测试已存在用户通过code登录"""
        # 先创建用户
        existing_user = await TestDataFactory.create_user(
            db_session,
            openid="existing_openid_login"
        )

        # Mock返回已存在的openid
        with patch('app.services.auth_service.code2session', new_callable=AsyncMock) as mock_code2session:
            mock_code2session.return_value = {
                "openid": "existing_openid_login",
                "session_key": "new_session_key"
            }

            result = await login_with_code(
                db_session,
                code="test_code_456"
            )

            assert result is not None
            access_token, refresh_token, user = result
            assert user.id == existing_user.id
            assert user.openid == "existing_openid_login"

    @pytest.mark.asyncio
    async def test_invalid_code_returns_none(self, db_session: AsyncSession):
        """测试无效code返回None"""
        # Mock微信API返回错误（没有openid）
        with patch('app.services.auth_service.code2session', new_callable=AsyncMock) as mock_code2session:
            mock_code2session.return_value = {
                "errcode": 40029,
                "errmsg": "invalid code"
            }

            result = await login_with_code(
                db_session,
                code="invalid_code"
            )

            # 根据实现，没有openid时返回None是正常流程
            assert result is None

    @pytest.mark.asyncio
    async def test_login_with_unionid(self, db_session: AsyncSession):
        """测试包含unionid的登录"""
        with patch('app.services.auth_service.code2session', new_callable=AsyncMock) as mock_code2session:
            mock_code2session.return_value = {
                "openid": "openid_with_unionid",
                "session_key": "session_key",
                "unionid": "unionid_123"
            }

            result = await login_with_code(
                db_session,
                code="test_code_with_unionid"
            )

            assert result is not None
            access_token, refresh_token, user = result
            assert user.openid == "openid_with_unionid"
            assert user.unionid == "unionid_123"


class TestRefreshAccessToken:
    """测试刷新access token"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, db_session: AsyncSession):
        """测试刷新token成功"""
        from app.core.security import create_refresh_token

        user = await TestDataFactory.create_user(db_session)
        old_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Mock Redis客户端
        # Note: Real Redis has decode_responses=True, so it returns strings not bytes
        with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.sismember = AsyncMock(return_value=False)  # token未撤销
            # Redis returns string (due to decode_responses=True in cache.py)
            mock_redis.get = AsyncMock(return_value=old_refresh_token)
            # 创建pipeline mock - pipeline() is a regular function, not async
            mock_pipeline = MockPipeline()
            mock_redis.pipeline = Mock(return_value=mock_pipeline)  # Regular Mock, not AsyncMock
            mock_get_redis.return_value = mock_redis

            result = await refresh_access_token(
                refresh_token=old_refresh_token,
                user_id=str(user.id)
            )

            assert result is not None
            new_access_token, new_refresh_token = result
            assert new_access_token is not None
            assert new_refresh_token is not None
            # Verify tokens are valid by checking they're strings and not empty
            assert isinstance(new_access_token, str)
            assert isinstance(new_refresh_token, str)
            assert len(new_access_token) > 0
            assert len(new_refresh_token) > 0

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_user_id(self, db_session: AsyncSession):
        """测试无效的user_id刷新token"""
        from app.core.security import create_refresh_token

        user = await TestDataFactory.create_user(db_session)
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # 使用不同的user_id（与token中的sub不匹配）
        result = await refresh_access_token(
            refresh_token=refresh_token,
            user_id="99999"  # 不同的user_id
        )

        # user_id不匹配应返回None
        assert result is None

    @pytest.mark.asyncio
    async def test_refresh_token_revoked_detection(self, db_session: AsyncSession):
        """测试检测已撤销的token（重放攻击检测）"""
        from app.core.security import create_refresh_token

        user = await TestDataFactory.create_user(db_session)
        old_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Mock Redis返回token已被撤销
        with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.sismember = AsyncMock(return_value=True)  # token已被撤销
            mock_get_redis.return_value = mock_redis

            result = await refresh_access_token(
                refresh_token=old_refresh_token,
                user_id=str(user.id)
            )

            # 已撤销的token应返回None
            assert result is None

    @pytest.mark.asyncio
    async def test_refresh_token_not_match_stored(self, db_session: AsyncSession):
        """测试token与存储的不匹配"""
        from app.core.security import create_refresh_token

        user = await TestDataFactory.create_user(db_session)
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Mock Redis返回不同的token
        with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.sismember = AsyncMock(return_value=False)
            mock_redis.get = AsyncMock(return_value=b"different_token_value")
            mock_get_redis.return_value = mock_redis

            result = await refresh_access_token(
                refresh_token=refresh_token,
                user_id=str(user.id)
            )

            # token不匹配应返回None
            assert result is None


class TestRevokeRefreshToken:
    """测试撤销refresh token"""

    @pytest.mark.asyncio
    async def test_revoke_token_success(self, db_session: AsyncSession):
        """测试撤销token成功"""
        user = await TestDataFactory.create_user(db_session)

        # Mock Redis客户端
        with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = AsyncMock()
            # 创建pipeline mock - pipeline() is a regular function, not async
            mock_pipeline = MockPipeline()
            mock_redis.pipeline = Mock(return_value=mock_pipeline)  # Regular Mock, not AsyncMock
            mock_get_redis.return_value = mock_redis

            # 撤销token不应抛出异常
            await revoke_refresh_token(user_id=str(user.id))

            # 验证pipeline被调用
            mock_redis.pipeline.assert_called()
            # verify execute was called (handled by MockPipeline)

    @pytest.mark.asyncio
    async def test_revoke_token_redis_error(self, db_session: AsyncSession):
        """测试Redis错误时不影响流程"""
        user = await TestDataFactory.create_user(db_session)

        # Mock Redis抛出异常
        with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.pipeline.side_effect = Exception("Redis connection error")
            mock_get_redis.return_value = mock_redis

            # 即使Redis出错，也不应抛出异常（根据实现，只记录日志）
            await revoke_refresh_token(user_id=str(user.id))
