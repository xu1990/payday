"""
Auth service phone login tests - TDD approach
Tests for phone number binding and login with phone_code parameter
"""
import pytest
from unittest.mock import AsyncMock, patch, Mock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import (
    get_or_create_user,
    login_with_code,
    bind_phone_to_user,
)
from app.models.user import User
from tests.test_utils import TestDataFactory


class MockPipeline:
    """Mock Redis pipeline for testing"""

    def __init__(self):
        self.operations = []

    def sadd(self, *args):
        self.operations.append(('sadd', args))
        return self

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
        return []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestBindPhoneToUser:
    """测试绑定手机号到用户"""

    @pytest.mark.asyncio
    async def test_bind_phone_to_new_user(self, db_session: AsyncSession):
        """测试为新用户绑定手机号"""
        # 创建一个没有手机号的用户
        user = await TestDataFactory.create_user(
            db_session,
            phone_number=None,
            phone_verified=0
        )

        # 绑定手机号
        phone = "13800138000"
        result = await bind_phone_to_user(
            db_session,
            user_id=str(user.id),
            phone_number=phone
        )

        assert result is True

        # 刷新并验证用户数据
        await db_session.refresh(user)
        assert user.phone_number is not None
        assert user.phone_number != phone  # 应该是加密的
        assert user.phone_verified == 1

    @pytest.mark.asyncio
    async def test_bind_phone_already_verified(self, db_session: AsyncSession):
        """测试已验证手机号不允许更改"""
        from app.core.exceptions import BusinessException
        from app.utils.encryption import encrypt_amount

        # 创建一个已有手机号的用户（使用正确的加密格式）
        encrypted_phone, salt = encrypt_amount("13900139000")
        phone_with_salt = f"{encrypted_phone}:{salt}"

        user = await TestDataFactory.create_user(
            db_session,
            phone_number=phone_with_salt,
            phone_verified=1
        )

        # 尝试绑定新手机号
        with pytest.raises(BusinessException) as exc_info:
            await bind_phone_to_user(
                db_session,
                user_id=str(user.id),
                phone_number="13800138000"
            )

        assert "手机号已验证" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_bind_phone_user_not_found(self, db_session: AsyncSession):
        """测试用户不存在"""
        from app.core.exceptions import NotFoundException

        with pytest.raises(NotFoundException) as exc_info:
            await bind_phone_to_user(
                db_session,
                user_id="nonexistent_user_id",
                phone_number="13800138000"
            )

        assert "用户不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_bind_phone_invalid_format(self, db_session: AsyncSession):
        """测试无效的手机号格式"""
        from app.core.exceptions import ValidationException

        user = await TestDataFactory.create_user(db_session)

        with pytest.raises(ValidationException) as exc_info:
            await bind_phone_to_user(
                db_session,
                user_id=str(user.id),
                phone_number="123"  # 太短
            )

        assert "手机号格式" in str(exc_info.value)


class TestLoginWithPhoneCode:
    """测试使用phone_code登录"""

    @pytest.mark.asyncio
    async def test_login_with_phone_code_new_user(self, db_session: AsyncSession):
        """测试新用户使用phone_code登录"""
        phone = "13800138000"

        # Mock code2session 和 get_phone_number_from_wechat
        with patch('app.services.auth_service.code2session', new_callable=AsyncMock) as mock_code2session, \
             patch('app.services.auth_service.get_phone_number_from_wechat', new_callable=AsyncMock) as mock_get_phone:

            mock_code2session.return_value = {
                "openid": "new_openid_with_phone",
                "session_key": "session_key",
                "unionid": None
            }
            mock_get_phone.return_value = phone

            # Mock Redis
            with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
                mock_redis = AsyncMock()
                mock_pipeline = MockPipeline()
                mock_redis.pipeline = Mock(return_value=mock_pipeline)
                mock_get_redis.return_value = mock_redis

                result = await login_with_code(
                    db_session,
                    code="test_code",
                    phone_code="phone_code_123"
                )

                assert result is not None
                access_token, refresh_token, user = result
                assert isinstance(user, User)
                assert user.phone_number is not None
                assert user.phone_verified == 1

                # 验证手机号已加密（不是明文）
                assert user.phone_number != phone

                # 验证调用
                mock_get_phone.assert_called_once_with("phone_code_123")

    @pytest.mark.asyncio
    async def test_login_with_phone_code_existing_phone(self, db_session: AsyncSession):
        """测试手机号已存在时关联到现有用户"""
        from app.utils.encryption import encrypt_amount

        phone = "13900139000"

        # 创建一个已有该手机号的用户（使用正确的加密格式）
        encrypted_phone, salt = encrypt_amount(phone)
        phone_with_salt = f"{encrypted_phone}:{salt}"

        existing_user = await TestDataFactory.create_user(
            db_session,
            phone_number=phone_with_salt,
            phone_verified=1
        )

        # Mock code2session 返回新的 openid
        with patch('app.services.auth_service.code2session', new_callable=AsyncMock) as mock_code2session, \
             patch('app.services.auth_service.get_phone_number_from_wechat', new_callable=AsyncMock) as mock_get_phone:

            mock_code2session.return_value = {
                "openid": "different_openid",  # 不同的 openid
                "session_key": "session_key",
                "unionid": None
            }
            mock_get_phone.return_value = phone

            # Mock Redis
            with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
                mock_redis = AsyncMock()
                mock_pipeline = MockPipeline()
                mock_redis.pipeline = Mock(return_value=mock_pipeline)
                mock_get_redis.return_value = mock_redis

                result = await login_with_code(
                    db_session,
                    code="test_code",
                    phone_code="phone_code_456"
                )

                assert result is not None
                access_token, refresh_token, user = result
                # 应返回已有手机号的用户
                assert user.id == existing_user.id

    @pytest.mark.asyncio
    async def test_login_without_phone_code_fallback(self, db_session: AsyncSession):
        """测试不提供phone_code时的回退行为（原有逻辑）"""
        # Mock code2session
        with patch('app.services.auth_service.code2session', new_callable=AsyncMock) as mock_code2session:
            mock_code2session.return_value = {
                "openid": "openid_without_phone",
                "session_key": "session_key",
                "unionid": None
            }

            # Mock Redis
            with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
                mock_redis = AsyncMock()
                mock_pipeline = MockPipeline()
                mock_redis.pipeline = Mock(return_value=mock_pipeline)
                mock_get_redis.return_value = mock_redis

                result = await login_with_code(
                    db_session,
                    code="test_code"
                    # 不提供 phone_code
                )

                assert result is not None
                access_token, refresh_token, user = result
                assert isinstance(user, User)
                assert user.openid == "openid_without_phone"
                # 手机号应该为空（因为没提供phone_code）
                assert user.phone_number is None
                assert user.phone_verified == 0

    @pytest.mark.asyncio
    async def test_login_with_phone_code_wechat_error(self, db_session: AsyncSession):
        """测试微信获取手机号失败时的处理"""
        # Mock code2session 成功
        with patch('app.services.auth_service.code2session', new_callable=AsyncMock) as mock_code2session, \
             patch('app.services.auth_service.get_phone_number_from_wechat', new_callable=AsyncMock) as mock_get_phone:

            mock_code2session.return_value = {
                "openid": "openid_with_phone_error",
                "session_key": "session_key",
                "unionid": None
            }
            # 微信获取手机号失败
            mock_get_phone.return_value = None

            # Mock Redis
            with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
                mock_redis = AsyncMock()
                mock_pipeline = MockPipeline()
                mock_redis.pipeline = Mock(return_value=mock_pipeline)
                mock_get_redis.return_value = mock_redis

                result = await login_with_code(
                    db_session,
                    code="test_code",
                    phone_code="invalid_phone_code"
                )

                # 应该继续登录流程，但不绑定手机号
                assert result is not None
                access_token, refresh_token, user = result
                assert user.phone_number is None
                assert user.phone_verified == 0

    @pytest.mark.asyncio
    async def test_login_with_phone_code_bind_to_current_user(self, db_session: AsyncSession):
        """测试将手机号绑定到当前登录用户"""
        phone = "13700137000"

        # 创建一个已有用户（没有手机号）
        existing_user = await TestDataFactory.create_user(
            db_session,
            openid="existing_user_no_phone",
            phone_number=None,
            phone_verified=0
        )

        # Mock code2session 返回已有用户的 openid
        with patch('app.services.auth_service.code2session', new_callable=AsyncMock) as mock_code2session, \
             patch('app.services.auth_service.get_phone_number_from_wechat', new_callable=AsyncMock) as mock_get_phone:

            mock_code2session.return_value = {
                "openid": "existing_user_no_phone",
                "session_key": "session_key",
                "unionid": None
            }
            mock_get_phone.return_value = phone

            # Mock Redis
            with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
                mock_redis = AsyncMock()
                mock_pipeline = MockPipeline()
                mock_redis.pipeline = Mock(return_value=mock_pipeline)
                mock_get_redis.return_value = mock_redis

                result = await login_with_code(
                    db_session,
                    code="test_code",
                    phone_code="phone_code_bind"
                )

                assert result is not None
                access_token, refresh_token, user = result
                # 应返回已有用户
                assert user.id == existing_user.id
                # 手机号应该已绑定
                assert user.phone_number is not None
                assert user.phone_verified == 1
