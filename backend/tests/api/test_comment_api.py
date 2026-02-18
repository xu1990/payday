"""
评论 API 集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.mark.asyncio
async def test_create_comment(db_session: AsyncSession, user_headers: dict, test_post):
    """测试创建评论"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        comment_data = {
            "post_id": str(test_post.id),
            "content": "这是一条测试评论"
        }
        response = await client.post(
            "/api/v1/comments",
            headers=user_headers,
            json=comment_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "这是一条测试评论"


@pytest.mark.asyncio
async def test_get_post_comments(db_session: AsyncSession, test_post):
    """测试获取帖子评论列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/comments/post/{test_post.id}")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data


@pytest.mark.asyncio
async def test_delete_comment(db_session: AsyncSession, user_headers: dict, test_comment):
    """测试删除评论"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/comments/{test_comment.id}",
            headers=user_headers
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_like_comment(db_session: AsyncSession, user_headers: dict, test_comment):
    """测试点赞评论"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/likes/comment/{test_comment.id}",
            headers=user_headers
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_comment_replies(db_session: AsyncSession, test_comment):
    """测试获取评论回复"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/comments/{test_comment.id}/replies")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
