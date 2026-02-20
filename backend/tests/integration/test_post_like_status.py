"""
Integration tests for post like status in API responses
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_post_list_response_includes_is_liked_for_authenticated(
    async_client, db_session: AsyncSession, test_user: User
):
    """Integration test: POST /api/v1/posts returns is_liked for authenticated users"""
    # Create another user for the post
    from tests.test_utils import TestDataFactory
    other_user = await TestDataFactory.create_user(db_session, openid="other_user_openid")

    # Create test post with correct status and risk_status
    post = Post(
        user_id=str(other_user.id),
        anonymous_name="Other User",
        content="Test post",
        status="normal",  # correct: status should be "normal"
        risk_status="approved",  # correct: risk_status should be "approved"
        visibility="public"  # correct: visibility should be "public"
    )
    db_session.add(post)
    await db_session.flush()  # Flush to generate defaults and ID
    await db_session.commit()

    # Create like from test_user
    like = Like(
        user_id=str(test_user.id),
        target_type="post",
        target_id=post.id
    )
    db_session.add(like)
    await db_session.commit()

    # Create token for test_user
    token = create_access_token(data={"sub": str(test_user.id)})

    # Make authenticated request
    response = await async_client.get(
        "/api/v1/posts?sort=latest&limit=20&offset=0",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    posts = data["details"]  # posts array is directly in details
    assert len(posts) > 0

    # Find the post we created
    liked_post = next((p for p in posts if p["id"] == post.id), None)
    assert liked_post is not None, f"Post {post.id} not found in response. Found posts: {[p['id'] for p in posts]}"
    assert liked_post["is_liked"] is True


@pytest.mark.asyncio
async def test_post_list_response_is_liked_false_for_unauthenticated(
    async_client, db_session: AsyncSession, test_user: User
):
    """Integration test: POST /api/v1/posts returns is_liked=False for unauthenticated users"""
    # Create another user for the post
    from tests.test_utils import TestDataFactory
    other_user = await TestDataFactory.create_user(db_session, openid="other_user_openid2")

    # Create test post
    post = Post(
        user_id=str(other_user.id),
        anonymous_name="Other User",
        content="Test post",
        status="normal",
        risk_status="approved",
        visibility="public"
    )
    db_session.add(post)
    await db_session.flush()  # Flush to generate defaults and ID
    await db_session.commit()

    # Create like from test_user
    like = Like(
        user_id=str(test_user.id),
        target_type="post",
        target_id=post.id
    )
    db_session.add(like)
    await db_session.commit()

    # Make UNAUTHENTICATED request (no token)
    response = await async_client.get(
        "/api/v1/posts?sort=latest&limit=20&offset=0"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    posts = data["details"]  # posts array is directly in details
    assert len(posts) > 0

    # Find the post we created
    test_post = next((p for p in posts if p["id"] == post.id), None)
    assert test_post is not None
    # Unauthenticated users should always see is_liked=False
    assert test_post["is_liked"] is False


@pytest.mark.asyncio
async def test_post_detail_response_includes_is_liked(
    async_client, db_session: AsyncSession, test_user: User
):
    """Integration test: GET /api/v1/posts/{id} returns is_liked"""
    # Create another user for the post
    from tests.test_utils import TestDataFactory
    other_user = await TestDataFactory.create_user(db_session, openid="other_user_openid3")

    # Create test post
    post = Post(
        user_id=str(other_user.id),
        anonymous_name="Other User",
        content="Test post detail",
        status="normal",
        risk_status="approved",
        visibility="public"
    )
    db_session.add(post)
    await db_session.flush()  # Flush to generate defaults and ID
    await db_session.commit()

    # Create like from test_user
    like = Like(
        user_id=str(test_user.id),
        target_type="post",
        target_id=post.id
    )
    db_session.add(like)
    await db_session.commit()

    # Create token for test_user
    token = create_access_token(data={"sub": str(test_user.id)})

    # Make authenticated request
    response = await async_client.get(
        f"/api/v1/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    post_data = data["details"]  # post object is directly in details
    assert post_data["id"] == post.id
    assert post_data["is_liked"] is True


@pytest.mark.asyncio
async def test_post_detail_response_is_liked_false_when_not_liked(
    async_client, db_session: AsyncSession, test_user: User
):
    """Integration test: GET /api/v1/posts/{id} returns is_liked=False when user hasn't liked"""
    # Create another user for the post
    from tests.test_utils import TestDataFactory
    other_user = await TestDataFactory.create_user(db_session, openid="other_user_openid4")

    # Create test post WITHOUT creating a like
    post = Post(
        user_id=str(other_user.id),
        anonymous_name="Other User",
        content="Test post not liked",
        status="normal",
        risk_status="approved",
        visibility="public"
    )
    db_session.add(post)
    await db_session.flush()  # Flush to generate defaults and ID
    await db_session.commit()

    # Create token for test_user
    token = create_access_token(data={"sub": str(test_user.id)})

    # Make authenticated request
    response = await async_client.get(
        f"/api/v1/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    post_data = data["details"]  # post object is directly in details
    assert post_data["id"] == post.id
    assert post_data["is_liked"] is False
