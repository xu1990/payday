"""
单元测试 - 依赖注入模块 (app.core.deps)
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.core.deps import (
    get_current_user,
    get_current_admin,
    require_permission,
    verify_csrf_token,
    verify_request_signature,
    rate_limit_general,
    rate_limit_login,
    rate_limit_post,
    rate_limit_comment,
)
from app.models.user import User
from app.models.admin import AdminUser


class TestGetCurrentUser:
    """测试获取当前用户依赖"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, db_session):
        """测试成功获取当前用户"""
        # 创建测试用户
        from tests.test_utils import TestDataFactory

        user = await TestDataFactory.create_user(db_session)

        # Mock credentials
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.scheme = "bearer"
        mock_credentials.credentials = "valid_token"

        # Mock decode_token to return user_id
        with patch('app.core.deps.decode_token', return_value={"sub": str(user.id)}):
            result_user = await get_current_user(db_session, mock_credentials)
            assert result_user.id == user.id
            assert result_user.status == "normal"

    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self, db_session):
        """测试没有提供认证信息"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, None)
        assert exc_info.value.status_code == 401
        assert "未提供认证信息" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_wrong_scheme(self, db_session):
        """测试错误的认证方案"""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.scheme = "Basic"
        mock_credentials.credentials = "some_token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, mock_credentials)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session):
        """测试无效token"""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.scheme = "bearer"
        mock_credentials.credentials = "invalid_token"

        with patch('app.core.deps.decode_token', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(db_session, mock_credentials)
            assert "无效或过期的 token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, db_session):
        """测试用户不存在"""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.scheme = "bearer"
        mock_credentials.credentials = "valid_token"

        with patch('app.core.deps.decode_token', return_value={"sub": "nonexistent_user_id"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(db_session, mock_credentials)
            assert "用户不存在或已禁用" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_disabled_user(self, db_session):
        """测试用户已禁用"""
        from tests.test_utils import TestDataFactory

        user = await TestDataFactory.create_user(db_session)
        user.status = "disabled"
        await db_session.commit()

        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.scheme = "bearer"
        mock_credentials.credentials = "valid_token"

        with patch('app.core.deps.decode_token', return_value={"sub": str(user.id)}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(db_session, mock_credentials)
            assert "用户不存在或已禁用" in exc_info.value.detail


class TestGetCurrentAdmin:
    """测试获取当前管理员依赖"""

    @pytest.mark.asyncio
    async def test_get_current_admin_success(self, db_session):
        """测试成功获取当前管理员"""
        from app.core.security import hash_password
        from app.models.admin import AdminUser

        admin = AdminUser(
            username="test_admin",
            password_hash=hash_password("password"),
            role="admin",
            is_active="1",
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.scheme = "bearer"
        mock_credentials.credentials = "valid_token"

        with patch('app.core.deps.decode_token', return_value={"sub": str(admin.id), "scope": "admin"}):
            result_admin = await get_current_admin(db_session, mock_credentials)
            assert result_admin.id == admin.id
            assert result_admin.role == "admin"

    @pytest.mark.asyncio
    async def test_get_current_admin_no_credentials(self, db_session):
        """测试没有提供认证信息"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin(db_session, None)
        assert exc_info.value.status_code == 401
        assert "未提供认证信息" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_admin_invalid_scope(self, db_session):
        """测试token scope不是admin"""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.scheme = "bearer"
        mock_credentials.credentials = "valid_token"

        with patch('app.core.deps.decode_token', return_value={"sub": "admin_id", "scope": "user"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_admin(db_session, mock_credentials)
            assert "无效或非管理员 token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_admin_not_found(self, db_session):
        """测试管理员不存在"""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.scheme = "bearer"
        mock_credentials.credentials = "valid_token"

        with patch('app.core.deps.decode_token', return_value={"sub": "nonexistent_id", "scope": "admin"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_admin(db_session, mock_credentials)
            assert "管理员不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_admin_disabled(self, db_session):
        """测试管理员账户已禁用"""
        from app.core.security import hash_password
        from app.models.admin import AdminUser

        admin = AdminUser(
            username="test_admin",
            password_hash=hash_password("password"),
            role="admin",
            is_active="0",  # 禁用
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.scheme = "bearer"
        mock_credentials.credentials = "valid_token"

        with patch('app.core.deps.decode_token', return_value={"sub": str(admin.id), "scope": "admin"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_admin(db_session, mock_credentials)
            assert exc_info.value.status_code == 403
            assert "管理员账户已被禁用" in exc_info.value.detail


class TestRequirePermission:
    """测试权限检查依赖"""

    @pytest.mark.asyncio
    async def test_require_permission_superadmin_pass(self):
        """测试superadmin角色通过所有权限检查"""
        from app.core.security import hash_password
        from app.models.admin import AdminUser

        admin = AdminUser(
            username="superadmin",
            password_hash=hash_password("password"),
            role="superadmin",
        )

        check_superadmin = require_permission("superadmin")
        result = await check_superadmin(admin)
        assert result is True

    @pytest.mark.asyncio
    async def test_require_permission_admin_pass(self):
        """测试admin角色通过admin权限检查"""
        from app.core.security import hash_password
        from app.models.admin import AdminUser

        admin = AdminUser(
            username="admin",
            password_hash=hash_password("password"),
            role="admin",
        )

        check_admin = require_permission("admin")
        result = await check_admin(admin)
        assert result is True

    @pytest.mark.asyncio
    async def test_require_permission_admin_fail_for_superadmin(self):
        """测试admin角色无法通过superadmin权限检查"""
        from app.core.security import hash_password
        from app.models.admin import AdminUser

        admin = AdminUser(
            username="admin",
            password_hash=hash_password("password"),
            role="admin",
        )

        check_superadmin = require_permission("superadmin")
        with pytest.raises(HTTPException) as exc_info:
            await check_superadmin(admin)
        assert exc_info.value.status_code == 403
        assert "权限不足" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_permission_default_role(self):
        """测试默认角色是admin"""
        from app.core.security import hash_password
        from app.models.admin import AdminUser

        # 没有role属性的管理员，默认是admin
        admin = AdminUser(
            username="admin",
            password_hash=hash_password("password"),
        )
        # 不设置role，测试默认值

        check_admin = require_permission("admin")
        result = await check_admin(admin)
        assert result is True


class TestVerifyCSRFToken:
    """测试CSRF token验证"""

    @pytest.mark.asyncio
    async def test_verify_csrf_safe_method_get(self):
        """测试GET请求跳过CSRF验证"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.query_params = {}

        from app.core.security import hash_password
        from app.models.admin import AdminUser
        admin = AdminUser(
            username="admin",
            password_hash=hash_password("password"),
            role="admin",
        )

        result = await verify_csrf_token(mock_request, admin)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_csrf_safe_method_with_readonly_params(self):
        """测试GET请求带只读参数跳过CSRF验证"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.query_params = {"page": "1", "limit": "10", "search": "test"}

        from app.core.security import hash_password
        from app.models.admin import AdminUser
        admin = AdminUser(
            username="admin",
            password_hash=hash_password("password"),
            role="admin",
        )

        result = await verify_csrf_token(mock_request, admin)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_csrf_safe_method_with_suspicious_params(self):
        """测试GET请求带可疑参数需要CSRF验证"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.query_params = {"action": "delete", "id": "123"}
        mock_request.headers = {}

        from app.core.security import hash_password
        from app.models.admin import AdminUser
        admin = AdminUser(
            username="admin",
            password_hash=hash_password("password"),
            role="admin",
        )

        # Mock csrf_manager to return False (invalid token)
        with patch('app.core.deps.csrf_manager') as mock_csrf:
            mock_csrf.validate_token = AsyncMock(return_value=False)

            from app.core.csrf import CSRFException
            with pytest.raises(CSRFException):
                await verify_csrf_token(mock_request, admin)

    @pytest.mark.asyncio
    async def test_verify_csrf_post_requires_token(self):
        """测试POST请求需要CSRF token"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {}

        from app.core.security import hash_password
        from app.models.admin import AdminUser
        admin = AdminUser(
            username="admin",
            password_hash=hash_password("password"),
            role="admin",
        )

        # Mock csrf_manager to return False
        with patch('app.core.deps.csrf_manager') as mock_csrf:
            mock_csrf.validate_token = AsyncMock(return_value=False)

            from app.core.csrf import CSRFException
            with pytest.raises(CSRFException):
                await verify_csrf_token(mock_request, admin)


class TestVerifyRequestSignature:
    """测试请求签名验证"""

    @pytest.mark.asyncio
    async def test_verify_signature_skip_when_missing(self):
        """测试没有签名头部时跳过验证"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"

        result = await verify_request_signature(mock_request, None, None, None)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_signature_valid(self):
        """测试有效签名"""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/test"
        mock_request.json = AsyncMock(return_value={"param": "value"})

        # Mock signature verification
        with patch('app.core.deps.verify_timestamp', return_value=True):
            with patch('app.core.deps.verify_signature', return_value=True):
                result = await verify_request_signature(
                    mock_request,
                    x_timestamp="1234567890",
                    x_nonce="abc123",
                    x_signature="valid_signature"
                )
                assert result is True

    @pytest.mark.asyncio
    async def test_verify_signature_invalid_timestamp(self):
        """测试无效时间戳"""
        mock_request = MagicMock(spec=Request)

        from app.core.exceptions import ValidationException
        with patch('app.core.deps.verify_timestamp') as mock_verify:
            mock_verify.side_effect = ValidationException("Timestamp expired")

            with pytest.raises(ValidationException):
                await verify_request_signature(
                    mock_request,
                    x_timestamp="old_timestamp",
                    x_nonce="abc123",
                    x_signature="some_signature"
                )


class TestRateLimits:
    """测试速率限制依赖"""

    @pytest.mark.asyncio
    async def test_rate_limit_general(self):
        """测试一般速率限制"""
        mock_request = MagicMock(spec=Request)

        with patch('app.core.deps.get_client_identifier', return_value="test_ip"):
            with patch('app.core.deps.RATE_LIMIT_GENERAL') as mock_rate:
                mock_rate.check = AsyncMock(return_value=True)
                result = await rate_limit_general(mock_request)
                assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_login(self):
        """测试登录速率限制"""
        mock_request = MagicMock(spec=Request)

        with patch('app.core.deps.get_client_identifier', return_value="test_ip"):
            with patch('app.core.deps.RATE_LIMIT_LOGIN') as mock_rate:
                mock_rate.check = AsyncMock(return_value=True)
                result = await rate_limit_login(mock_request)
                assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_post(self):
        """测试发帖速率限制"""
        mock_request = MagicMock(spec=Request)

        with patch('app.core.deps.get_client_identifier', return_value="test_ip"):
            with patch('app.core.deps.RATE_LIMIT_POST') as mock_rate:
                mock_rate.check = AsyncMock(return_value=True)
                result = await rate_limit_post(mock_request)
                assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_comment(self):
        """测试评论速率限制"""
        mock_request = MagicMock(spec=Request)

        with patch('app.core.deps.get_client_identifier', return_value="test_ip"):
            with patch('app.core.deps.RATE_LIMIT_COMMENT') as mock_rate:
                mock_rate.check = AsyncMock(return_value=True)
                result = await rate_limit_comment(mock_request)
                assert result is True
