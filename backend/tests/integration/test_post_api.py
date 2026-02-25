"""
Integration tests for post API responses
"""
import pytest
from app.core.security import create_access_token
from app.models.post import Post
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.integration
async def test_post_list_includes_user_avatar(async_client, db_session: AsyncSession, test_user: User):
    """Integration test: POST /api/v1/posts returns user_avatar field"""
    from tests.test_utils import TestDataFactory

    # Create another user with an avatar
    other_user = await TestDataFactory.create_user(
        db_session,
        openid="avatar_test_user",
        avatar="https://example.com/avatar.jpg"
    )

    # Create test post
    post = Post(
        user_id=str(other_user.id),
        anonymous_name="User With Avatar",
        user_avatar=other_user.avatar,  # Set user_avatar from user
        content="Test post with avatar",
        status="normal",
        risk_status="approved",
        visibility="public"
    )
    db_session.add(post)
    await db_session.flush()
    await db_session.commit()

    # Get posts list - should include user_avatar field
    response = await async_client.get("/api/v1/posts?sort=latest&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    posts = data["details"]

    # Verify we have posts
    assert len(posts) > 0, "Should have at least one post"

    # Find the post we created
    test_post = next((p for p in posts if p["id"] == post.id), None)
    assert test_post is not None, f"Post {post.id} not found in response"

    # Check that user_avatar field exists
    assert "user_avatar" in test_post, "Post should have user_avatar field"
    # Check that it has the expected value
    assert test_post["user_avatar"] == "https://example.com/avatar.jpg"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_post_detail_includes_user_avatar(async_client, db_session: AsyncSession, test_user: User):
    """Integration test: GET /api/v1/posts/{id} returns user_avatar field"""
    from tests.test_utils import TestDataFactory

    # Create another user with an avatar
    other_user = await TestDataFactory.create_user(
        db_session,
        openid="avatar_detail_user",
        avatar="https://example.com/detail-avatar.jpg"
    )

    # Create test post
    post = Post(
        user_id=str(other_user.id),
        anonymous_name="Detail User",
        user_avatar=other_user.avatar,  # Set user_avatar from user
        content="Test post detail with avatar",
        status="normal",
        risk_status="approved",
        visibility="public"
    )
    db_session.add(post)
    await db_session.flush()
    await db_session.commit()

    # Get post detail
    response = await async_client.get(f"/api/v1/posts/{post.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    post_data = data["details"]

    # Verify post data
    assert post_data["id"] == post.id

    # Check that user_avatar field exists
    assert "user_avatar" in post_data, "Post detail should have user_avatar field"
    # Check that it has the expected value
    assert post_data["user_avatar"] == "https://example.com/detail-avatar.jpg"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_post_user_avatar_null_when_no_avatar(async_client, db_session: AsyncSession, test_user: User):
    """Integration test: user_avatar is None when user has no avatar set"""
    from tests.test_utils import TestDataFactory

    # Create another user without an avatar
    other_user = await TestDataFactory.create_user(
        db_session,
        openid="no_avatar_user"
        # avatar_url not set, should be None
    )

    # Create test post
    post = Post(
        user_id=str(other_user.id),
        anonymous_name="No Avatar User",
        content="Test post without avatar",
        status="normal",
        risk_status="approved",
        visibility="public"
    )
    db_session.add(post)
    await db_session.flush()
    await db_session.commit()

    # Get post detail
    response = await async_client.get(f"/api/v1/posts/{post.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    post_data = data["details"]

    # Check that user_avatar field exists but is None
    assert "user_avatar" in post_data, "Post should have user_avatar field"
    assert post_data["user_avatar"] is None, "user_avatar should be None when not set"
