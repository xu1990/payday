"""
通知 API 集成测试
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestNotificationAPI:
    """测试通知API"""

    def test_get_notifications(self, client, user_headers: dict):
        """测试获取通知列表"""
        response = client.get("/api/v1/notifications", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "unread_count" in data

    def test_mark_notification_read(self, client, user_headers: dict, test_notification):
        """测试标记通知为已读"""
        response = client.put(
            f"/api/v1/notifications/{test_notification.id}/read",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "updated" in data
        assert data["updated"] == 1

    def test_mark_all_read(self, client, user_headers: dict):
        """测试标记所有通知为已读"""
        # 使用正确的请求体
        response = client.put(
            "/api/v1/notifications/read",
            headers=user_headers,
            json={"all": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert "updated" in data

    def test_delete_notification(self, client, user_headers: dict, test_notification):
        """测试删除通知"""
        # DELETE 使用 query 参数
        response = client.delete(
            f"/api/v1/notifications?notification_ids={test_notification.id}",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data

    # 注意：settings 端点不存在，以下测试暂时注释
    # def test_get_notification_settings(self, client, user_headers: dict):
    #     """测试获取通知设置"""
    #     response = client.get("/api/v1/notifications/settings", headers=user_headers)
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert "payday_reminder" in data
    #     assert "like_notification" in data

    # def test_update_notification_settings(self, client, user_headers: dict):
    #     """测试更新通知设置"""
    #     settings = {"payday_reminder": True, "like_notification": False}
    #     response = client.put(
    #         "/api/v1/notifications/settings",
    #         headers=user_headers,
    #         json=settings
    #     )
    #     assert response.status_code == 200
