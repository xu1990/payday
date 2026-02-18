"""
通知 API 集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.mark.asyncio
async def test_get_notifications(db_session: AsyncSession, user_headers: dict):
    """测试获取通知列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/notifications", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "unread_count" in data


@pytest.mark.asyncio
async def test_mark_notification_read(db_session: AsyncSession, user_headers: dict, test_notification):
    """测试标记通知为已读"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/notifications/{test_notification.id}/read",
            headers=user_headers
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_mark_all_read(db_session: AsyncSession, user_headers: dict):
    """测试标记所有通知为已读"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/api/v1/notifications/read-all",
            headers=user_headers
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_notification(db_session: AsyncSession, user_headers: dict, test_notification):
    """测试删除通知"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/notifications/{test_notification.id}",
            headers=user_headers
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_notification_settings(db_session: AsyncSession, user_headers: dict):
    """测试获取通知设置"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/notifications/settings", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "payday_reminder" in data
        assert "like_notification" in data


@pytest.mark.asyncio
async def test_update_notification_settings(db_session: AsyncSession, user_headers: dict):
    """测试更新通知设置"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        settings = {"payday_reminder": True, "like_notification": False}
        response = await client.patch(
            "/api/v1/notifications/settings",
            headers=user_headers,
            json=settings
        )

        assert response.status_code == 200
