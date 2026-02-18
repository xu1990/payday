"""
发薪日配置 API 集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.mark.asyncio
async def test_create_payday_config(db_session: AsyncSession, user_headers: dict):
    """测试创建发薪日配置"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        config_data = {
            "job_name": "软件工程师",
            "payday": 25,
            "is_monthly": True
        }
        response = await client.post(
            "/api/v1/payday/config",
            headers=user_headers,
            json=config_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_name"] == "软件工程师"
        assert data["payday"] == 25


@pytest.mark.asyncio
async def test_get_payday_configs(db_session: AsyncSession, user_headers: dict):
    """测试获取发薪日配置列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/payday/config", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data


@pytest.mark.asyncio
async def test_update_payday_config(db_session: AsyncSession, user_headers: dict, test_payday_config):
    """测试更新发薪日配置"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/payday/config/{test_payday_config.id}",
            headers=user_headers,
            json={"job_name": "高级工程师", "payday": 28}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_name"] == "高级工程师"
        assert data["payday"] == 28


@pytest.mark.asyncio
async def test_delete_payday_config(db_session: AsyncSession, user_headers: dict, test_payday_config):
    """测试删除发薪日配置"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/payday/config/{test_payday_config.id}",
            headers=user_headers
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_next_payday(db_session: AsyncSession, user_headers: dict, test_payday_config):
    """测试获取下次发薪日"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/payday/next?config_id={test_payday_config.id}",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "next_payday" in data
        assert "days_remaining" in data
