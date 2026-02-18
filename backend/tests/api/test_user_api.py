"""
用户 API 集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User


@pytest.mark.asyncio
async def test_get_current_user_without_auth():
    """测试未认证时获取当前用户"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_with_auth(db_session: AsyncSession, user_headers: dict):
    """测试已认证时获取当前用户"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/users/me", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "nickname" in data


@pytest.mark.asyncio
async def test_update_user_profile(db_session: AsyncSession, user_headers: dict):
    """测试更新用户资料"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        update_data = {
            "nickname": "新昵称",
            "avatar": "https://example.com/new_avatar.jpg"
        }
        response = await client.patch(
            "/api/v1/users/me",
            headers=user_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nickname"] == "新昵称"


@pytest.mark.asyncio
async def test_get_user_by_id(db_session: AsyncSession, test_user: User):
    """测试通过 ID 获取用户信息"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/users/{test_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_get_user_stats(db_session: AsyncSession, user_headers: dict):
    """测试获取用户统计信息"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/users/me/stats", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "post_count" in data
        assert "salary_count" in data
