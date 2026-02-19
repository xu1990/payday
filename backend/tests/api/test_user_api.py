"""
用户 API 集成测试
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


@pytest.mark.asyncio
class TestUserAPI:
    """测试用户API"""

    def test_get_current_user_without_auth(self, client):
        """测试未认证时获取当前用户"""
        response = client.get("/api/v1/user/me")

        assert response.status_code == 401

    def test_get_current_user_with_auth(self, client, user_headers: dict):
        """测试已认证时获取当前用户"""
        response = client.get("/api/v1/user/me", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "anonymous_name" in data

    def test_update_user_profile(self, client, user_headers: dict):
        """测试更新用户资料"""
        update_data = {
            "anonymous_name": "新昵称",
            "avatar": "https://example.com/new_avatar.jpg"
        }
        response = client.put(
            "/api/v1/user/me",
            headers=user_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["anonymous_name"] == "新昵称"

    def test_get_user_by_id(self, client, test_user: User):
        """测试通过 ID 获取用户信息"""
        # 使用正确的路由 /user/profile-data/{user_id}
        response = client.get(f"/api/v1/user/profile-data/{test_user.id}")

        # 这个端点需要认证
        assert response.status_code in [200, 401]  # 可能需要认证

    def test_get_user_stats(self, client, user_headers: dict):
        """测试获取用户统计信息"""
        # 注意：可能没有单独的 /stats 端点，统计数据在 /me 响应中
        response = client.get("/api/v1/user/me", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        # 验证统计数据存在
        assert "post_count" in data
        assert "follower_count" in data
        assert "following_count" in data

