"""
单元测试 - CSRF 保护模块 (app.core.csrf)
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import Request

from app.core.csrf import (
    CSRFTokenManager,
    CSRFException,
    csrf_response,
    csrf_manager,
)


class TestCSRFTokenManager:
    """测试CSRF Token管理器"""

    @pytest.mark.asyncio
    async def test_generate_token(self):
        """测试生成CSRF token"""
        manager = CSRFTokenManager()
        token = await manager.generate_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_save_token_with_redis(self):
        """测试保存token到Redis"""
        manager = CSRFTokenManager()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)

        with patch('app.core.csrf.get_redis_client', return_value=mock_redis):
            token = "test_token_123"
            user_id = "user_456"

            await manager.save_token(token, user_id, ttl=3600)

            # 验证调用
            mock_redis.setex.assert_called_once_with("csrf:user_456", 3600, token)

    @pytest.mark.asyncio
    async def test_save_token_no_redis(self):
        """测试保存token - Redis不可用"""
        manager = CSRFTokenManager()

        with patch('app.core.csrf.get_redis_client', return_value=None):
            # 不应该抛出异常
            await manager.save_token("test_token", "user_id")
            # 通过 - 没有异常

    @pytest.mark.asyncio
    async def test_validate_token_valid(self):
        """测试验证有效token"""
        manager = CSRFTokenManager()
        token = "valid_token_123"
        user_id = "user_456"

        # Mock Redis返回存储的token（decode_responses=True意味着返回字符串）
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=token)

        # Mock request with valid header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-CSRF-Token": token}

        with patch('app.core.csrf.get_redis_client', return_value=mock_redis):
            result = await manager.validate_token(mock_request, user_id)
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_token_no_header(self):
        """测试验证token - 缺少header"""
        manager = CSRFTokenManager()

        # Mock request without header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}

        result = await manager.validate_token(mock_request, "user_id")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_token_no_redis(self):
        """测试验证token - Redis不可用"""
        manager = CSRFTokenManager()
        token = "test_token"

        # Mock request with header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-CSRF-Token": token}

        with patch('app.core.csrf.get_redis_client', return_value=None):
            result = await manager.validate_token(mock_request, "user_id")
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_token_no_stored_token(self):
        """测试验证token - Redis中没有存储的token"""
        manager = CSRFTokenManager()
        token = "test_token"

        # Mock request with header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-CSRF-Token": token}

        # Mock Redis返回None
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch('app.core.csrf.get_redis_client', return_value=mock_redis):
            result = await manager.validate_token(mock_request, "user_id")
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_token_mismatch(self):
        """测试验证token - token不匹配"""
        manager = CSRFTokenManager()

        # Mock request with header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-CSRF-Token": "received_token"}

        # Mock Redis返回不同的token
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="stored_token")

        with patch('app.core.csrf.get_redis_client', return_value=mock_redis):
            result = await manager.validate_token(mock_request, "user_id")
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_token(self):
        """测试删除token"""
        manager = CSRFTokenManager()
        user_id = "user_456"

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=True)

        with patch('app.core.csrf.get_redis_client', return_value=mock_redis):
            await manager.delete_token(user_id)
            mock_redis.delete.assert_called_once_with("csrf:user_456")

    @pytest.mark.asyncio
    async def test_delete_token_no_redis(self):
        """测试删除token - Redis不可用"""
        manager = CSRFTokenManager()

        with patch('app.core.csrf.get_redis_client', return_value=None):
            # 不应该抛出异常
            await manager.delete_token("user_id")
            # 通过 - 没有异常


class TestCSRFException:
    """测试CSRF异常"""

    def test_csrf_exception_default(self):
        """测试默认CSRF异常"""
        exc = CSRFException()
        assert exc.status_code == 403
        assert exc.detail == "CSRF token validation failed"

    def test_csrf_exception_custom_detail(self):
        """测试自定义详情的CSRF异常"""
        exc = CSRFException(detail="Custom CSRF error")
        assert exc.status_code == 403
        assert exc.detail == "Custom CSRF error"


class TestCSRFResponse:
    """测试CSRF响应函数"""

    def test_csrf_response_default(self):
        """测试默认CSRF响应"""
        response = csrf_response()
        assert response.status_code == 200
        content = response.body.decode()
        import json
        data = json.loads(content)
        assert data["success"] is True
        assert data["message"] == "OK"

    def test_csrf_response_with_token(self):
        """测试带token的CSRF响应"""
        token = "test_csrf_token"
        response = csrf_response(csrf_token=token)

        assert response.status_code == 200
        assert response.headers["X-CSRF-Token"] == token

    def test_csrf_response_custom_values(self):
        """测试自定义值的CSRF响应"""
        response = csrf_response(
            success=False,
            message="Error occurred",
            csrf_token="token123",
            status_code=400
        )

        assert response.status_code == 400
        assert response.headers["X-CSRF-Token"] == "token123"
        content = response.body.decode()
        import json
        data = json.loads(content)
        assert data["success"] is False
        assert data["message"] == "Error occurred"

    def test_csrf_response_without_token(self):
        """测试不带token的CSRF响应"""
        response = csrf_response(success=True, message="OK")

        assert "X-CSRF-Token" not in response.headers
