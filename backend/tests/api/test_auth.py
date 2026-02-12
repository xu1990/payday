"""
认证API端点测试

测试 /api/v1/auth/* 路由的HTTP端点：
- POST /api/v1/auth/login - 微信code登录
- POST /api/v1/auth/refresh - 刷新access token
- POST /api/v1/auth/logout - 登出（撤销refresh token）
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, Mock


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


class TestLoginEndpoint:
    """测试POST /api/v1/auth/login端点"""

    def test_login_success(self, client):
        """测试登录成功 - 使用有效的微信code"""
        with patch('app.services.auth_service.code2session', new_callable=AsyncMock) as mock_code2session, \
             patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:

            # Mock微信登录成功响应
            mock_code2session.return_value = {
                "openid": "test_openid_login_success",
                "session_key": "test_session_key"
            }

            mock_redis = MagicMock()
            mock_redis.setex = AsyncMock(return_value=True)
            mock_get_redis.return_value = mock_redis

            # 使用TestClient发送HTTP POST请求
            response = client.post("/api/v1/auth/login", json={"code": "test_code"})

            # 验证HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "user" in data
            assert data["user"]["anonymous_name"] is not None
            assert data["user"]["id"] is not None

    def test_login_missing_code(self, client):
        """测试登录失败 - 缺少code参数"""
        # 使用TestClient发送HTTP POST请求（缺少code）
        response = client.post("/api/v1/auth/login", json={})

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestRefreshTokenEndpoint:
    """测试POST /api/v1/auth/refresh端点"""

    def test_refresh_token_success(self, client, test_user):
        """测试刷新token成功 - 使用有效的refresh token"""
        from app.core.security import create_refresh_token

        # 创建一个有效的refresh token
        refresh_token = create_refresh_token(data={"sub": str(test_user.id)})

        with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            # Mock Redis返回有效的refresh token
            mock_redis.get = AsyncMock(return_value=refresh_token)
            mock_redis.sismember = AsyncMock(return_value=False)
            # Mock pipeline
            mock_redis.pipeline = Mock(return_value=MockPipeline())

            mock_get_redis.return_value = mock_redis

            # 使用TestClient发送HTTP POST请求
            response = client.post("/api/v1/auth/refresh", json={
                "refresh_token": refresh_token,
                "user_id": str(test_user.id)
            })

            # 验证HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data

    def test_refresh_token_invalid(self, client, test_user):
        """测试刷新token失败 - 使用无效的refresh token"""
        with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            # Mock Redis返回None（token不存在）
            mock_redis.get = AsyncMock(return_value=None)
            mock_get_redis.return_value = mock_redis

            # 使用TestClient发送HTTP POST请求
            response = client.post("/api/v1/auth/refresh", json={
                "refresh_token": "invalid_token_string",
                "user_id": str(test_user.id)
            })

            # 验证HTTP响应 - 应该返回401
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data


class TestLogoutEndpoint:
    """测试POST /api/v1/auth/logout端点"""

    def test_logout_success(self, client, user_headers, test_user):
        """测试登出成功 - 撤销refresh token"""
        with patch('app.services.auth_service.get_redis_client', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.delete = AsyncMock(return_value=1)
            # Mock pipeline
            mock_redis.pipeline = Mock(return_value=MockPipeline())
            mock_get_redis.return_value = mock_redis

            # 使用TestClient发送HTTP POST请求（需要认证）
            response = client.post("/api/v1/auth/logout", headers=user_headers)

            # 验证HTTP响应
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "登出成功"


class TestGetUserProfile:
    """测试GET /api/v1/user/me端点（获取当前用户信息）"""

    def test_get_user_profile_success(self, client, user_headers, test_user):
        """测试获取用户信息成功 - 使用有效token"""
        # 使用TestClient发送HTTP GET请求（需要认证）
        response = client.get("/api/v1/user/me", headers=user_headers)

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["anonymous_name"] is not None
        assert "avatar" in data

    def test_get_user_profile_unauthorized(self, client):
        """测试获取用户信息失败 - 未提供token"""
        # 使用TestClient发送HTTP GET请求（无认证）
        response = client.get("/api/v1/user/me")

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401
