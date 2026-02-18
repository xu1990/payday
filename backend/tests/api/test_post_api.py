"""
帖子 API 集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.models.post import Post


@pytest.mark.asyncio
async def test_create_post_without_auth():
    """测试未认证时创建帖子"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/posts",
            json={"content": "测试内容"}
        )

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_post_with_auth(db_session: AsyncSession, user_headers: dict, mock_yu_moderation):
    """测试已认证时创建帖子"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        post_data = {
            "content": "这是一个测试帖子",
            "images": [],
            "mood": "happy",
            "is_anonymous": False
        }
        response = await client.post(
            "/api/v1/posts",
            headers=user_headers,
            json=post_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "这是一个测试帖子"
        assert data["mood"] == "happy"


@pytest.mark.asyncio
async def test_get_posts_list():
    """测试获取帖子列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/posts")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data


@pytest.mark.asyncio
async def test_get_post_by_id(db_session: AsyncSession, test_post: Post):
    """测试通过 ID 获取帖子详情"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/posts/{test_post.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_post.id)


@pytest.mark.asyncio
async def test_delete_post(db_session: AsyncSession, test_post: Post, user_headers: dict):
    """测试删除帖子"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/posts/{test_post.id}",
            headers=user_headers
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_like_post(db_session: AsyncSession, test_post: Post, user_headers: dict):
    """测试点赞帖子"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 点赞
        response = await client.post(
            f"/api/v1/likes/post/{test_post.id}",
            headers=user_headers
        )

        assert response.status_code == 200
