"""
工资记录 API 集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.mark.asyncio
async def test_create_salary_record(db_session: AsyncSession, user_headers: dict, test_payday_config):
    """测试创建工资记录"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        salary_data = {
            "config_id": test_payday_config.id,
            "amount": 15000,
            "actual_payday": "2026-02-15",
            "mood": "happy",
            "is_public": False
        }
        response = await client.post(
            "/api/v1/salary",
            headers=user_headers,
            json=salary_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 15000
        assert data["mood"] == "happy"


@pytest.mark.asyncio
async def test_create_salary_without_auth():
    """测试未认证时创建工资记录"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/salary", json={})

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_salary_records(db_session: AsyncSession, user_headers: dict, test_salary):
    """测试获取工资记录列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/salary", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_get_salary_by_id(db_session: AsyncSession, user_headers: dict, test_salary):
    """测试获取单条工资记录"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/salary/{test_salary.id}", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_salary.id)


@pytest.mark.asyncio
async def test_delete_salary(db_session: AsyncSession, user_headers: dict, test_salary):
    """测试删除工资记录"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/salary/{test_salary.id}",
            headers=user_headers
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_salary_mood(db_session: AsyncSession, user_headers: dict, test_salary):
    """测试更新工资心情"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/salary/{test_salary.id}",
            headers=user_headers,
            json={"mood": "excited"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "excited"
