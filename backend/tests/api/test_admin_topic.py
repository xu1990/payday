"""话题管理API测试"""
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.topic_service import create_topic


@pytest.mark.asyncio
class TestListTopicsEndpoint:
    """测试获取话题列表接口"""

    async def test_list_all_topics(self, client, test_admin: User, admin_headers: dict, db_session: AsyncSession):
        """测试获取所有话题"""
        await create_topic(db_session, name="话题1", sort_order=10)
        await create_topic(db_session, name="话题2", sort_order=5)

        response = client.get("/api/v1/admin/topics", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_list_active_only(self, client, test_admin: User, admin_headers: dict, db_session: AsyncSession):
        """测试仅获取启用的话题"""
        from app.services.topic_service import update_topic

        topic1 = await create_topic(db_session, name="启用话题")
        topic2 = await create_topic(db_session, name="禁用话题")
        await update_topic(db_session, topic2.id, is_active=False)

        response = client.get("/api/v1/admin/topics?active_only=true", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "启用话题"

    async def test_list_with_pagination(self, client, test_admin: User, admin_headers: dict, db_session: AsyncSession):
        """测试分页功能"""
        for i in range(5):
            await create_topic(db_session, name=f"话题{i}", sort_order=i)

        # 第一页：2条
        response = client.get("/api/v1/admin/topics?limit=2&offset=0", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    async def test_list_without_auth(self, client):
        """测试未认证用户获取列表"""
        response = client.get("/api/v1/admin/topics")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestCreateTopicEndpoint:
    """测试创建话题接口"""

    async def test_create_topic_success(self, client, test_admin: User, admin_headers: dict):
        """测试成功创建话题"""
        response = client.post(
            "/api/v1/admin/topics",
            json={
                "name": "测试话题",
                "description": "这是一个测试话题",
                "sort_order": 10,
            },
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "测试话题"
        assert data["description"] == "这是一个测试话题"
        assert data["sort_order"] == 10
        assert data["is_active"] is True
        assert data["post_count"] == 0

    async def test_create_topic_minimal(self, client, test_admin: User, admin_headers: dict):
        """测试仅提供必填字段"""
        response = client.post(
            "/api/v1/admin/topics",
            json={"name": "最小话题"},
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "最小话题"
        assert data["description"] is None
        assert data["sort_order"] == 0

    async def test_create_topic_with_cover(self, client, test_admin: User, admin_headers: dict):
        """测试创建带封面图的话题"""
        response = client.post(
            "/api/v1/admin/topics",
            json={
                "name": "封面话题",
                "cover_image": "https://example.com/cover.jpg",
            },
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cover_image"] == "https://example.com/cover.jpg"

    async def test_create_topic_validation_error(self, client, test_admin: User, admin_headers: dict):
        """测试验证错误"""
        # name 超过最大长度
        response = client.post(
            "/api/v1/admin/topics",
            json={"name": "a" * 51},  # 超过50字符
            headers=admin_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_topic_without_auth(self, client):
        """测试未认证用户创建话题"""
        response = client.post(
            "/api/v1/admin/topics",
            json={"name": "测试话题"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestGetTopicEndpoint:
    """测试获取单个话题接口"""

    async def test_get_existing_topic(self, client, test_admin: User, admin_headers: dict, db_session: AsyncSession):
        """测试获取已存在的话题"""
        topic = await create_topic(db_session, name="测试话题")

        response = client.get(f"/api/v1/admin/topics/{topic.id}", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == topic.id
        assert data["name"] == "测试话题"

    async def test_get_nonexistent_topic(self, client, test_admin: User, admin_headers: dict):
        """测试获取不存在的话题"""
        response = client.get(
            "/api/v1/admin/topics/nonexistent_id", headers=admin_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_topic_without_auth(self, client, db_session: AsyncSession):
        """测试未认证用户获取话题"""
        topic = await create_topic(db_session, name="测试话题")

        response = client.get(f"/api/v1/admin/topics/{topic.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestUpdateTopicEndpoint:
    """测试更新话题接口"""

    async def test_update_name(self, client, test_admin: User, admin_headers: dict, db_session: AsyncSession):
        """测试更新名称"""
        topic = await create_topic(db_session, name="原名称")

        response = client.put(
            f"/api/v1/admin/topics/{topic.id}",
            json={"name": "新名称"},
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "新名称"

    async def test_update_multiple_fields(self, client, test_admin: User, admin_headers: dict, db_session: AsyncSession):
        """测试更新多个字段"""
        topic = await create_topic(db_session, name="原名称", sort_order=0)

        response = client.put(
            f"/api/v1/admin/topics/{topic.id}",
            json={
                "name": "新名称",
                "description": "新描述",
                "sort_order": 100,
                "is_active": False,
            },
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "新名称"
        assert data["description"] == "新描述"
        assert data["sort_order"] == 100
        assert data["is_active"] is False

    async def test_update_nonexistent_topic(self, client, test_admin: User, admin_headers: dict):
        """测试更新不存在的话题"""
        response = client.put(
            "/api/v1/admin/topics/nonexistent_id",
            json={"name": "新名称"},
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_without_auth(self, client, test_admin: User, db_session: AsyncSession):
        """测试未认证用户更新话题"""
        topic = await create_topic(db_session, name="测试话题")

        response = client.put(
            f"/api/v1/admin/topics/{topic.id}",
            json={"name": "新名称"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestDeleteTopicEndpoint:
    """测试删除话题接口"""

    async def test_delete_topic_success(self, client, test_admin: User, admin_headers: dict, db_session: AsyncSession):
        """测试成功删除话题"""
        topic = await create_topic(db_session, name="测试话题")

        response = client.delete(f"/api/v1/admin/topics/{topic.id}", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted"] is True

    async def test_delete_nonexistent_topic(self, client, test_admin: User, admin_headers: dict):
        """测试删除不存在的话题"""
        response = client.delete(
            "/api/v1/admin/topics/nonexistent_id", headers=admin_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_without_auth(self, client, test_admin: User, db_session: AsyncSession):
        """测试未认证用户删除话题"""
        topic = await create_topic(db_session, name="测试话题")

        response = client.delete(f"/api/v1/admin/topics/{topic.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
