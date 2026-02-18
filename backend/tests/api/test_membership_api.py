"""
会员 API 集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.mark.asyncio
async def test_list_memberships():
    """测试获取会员套餐列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/membership")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_membership_by_id(db_session: AsyncSession, test_membership):
    """测试获取单个会员套餐"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/membership/{test_membership.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_membership.id)
        assert "name" in data
        assert "price" in data


@pytest.mark.asyncio
async def test_get_user_membership(db_session: AsyncSession, user_headers: dict):
    """测试获取用户会员状态"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/membership/my", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "is_member" in data
        assert "level" in data


@pytest.mark.asyncio
async def test_check_privilege(db_session: AsyncSession, user_headers: dict, test_membership):
    """测试检查会员特权"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/membership/check-privilege",
            headers=user_headers,
            json={"privilege": "advanced_stats"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "has_privilege" in data


@pytest.mark.asyncio
async def test_get_membership_benefits(db_session: AsyncSession, test_membership):
    """测试获取会员权益"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/membership/{test_membership.id}/benefits")

        assert response.status_code == 200
        data = response.json()
        assert "benefits" in data
