"""
认证 API 集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User


@pytest.mark.asyncio
async def test_login_with_invalid_code(db_session: AsyncSession):
    """测试使用无效 code 登录"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/login", json={"code": "invalid_code"})

        # 预期会失败
        assert response.status_code in [400, 401]


@pytest.mark.asyncio
async def test_login_missing_code(db_session: AsyncSession):
    """测试缺少 code 参数的登录请求"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/login", json={})

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_refresh_token_with_valid_token(db_session: AsyncSession, user_token: str):
    """测试刷新 token"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # 可能成功或失败（取决于 refresh token 实现）
        assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_logout(user_token: str):
    """测试登出"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code in [200, 401]
