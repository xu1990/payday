"""Test Post model with user_avatar field"""
from datetime import datetime

import pytest
from app.models.post import Post
from sqlalchemy import select


@pytest.mark.asyncio
async def test_post_creation_with_user_avatar(db_session):
    """Test creating a post with user_avatar"""
    post = Post(
        user_id="test_user_id",
        anonymous_name="Test User",
        user_avatar="https://example.com/avatar.jpg",
        content="Test content",
        status="normal",
        risk_status="approved",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    retrieved_post = await db_session.execute(
        select(Post).filter_by(id=post.id)
    )
    result = retrieved_post.scalar_one()
    assert result is not None
    assert result.user_avatar == "https://example.com/avatar.jpg"


@pytest.mark.asyncio
async def test_post_creation_without_user_avatar(db_session):
    """Test creating a post without user_avatar (nullable)"""
    post = Post(
        user_id="test_user_id",
        anonymous_name="Test User",
        user_avatar=None,
        content="Test content",
        status="normal",
        risk_status="approved",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    retrieved_post = await db_session.execute(
        select(Post).filter_by(id=post.id)
    )
    result = retrieved_post.scalar_one()
    assert result is not None
    assert result.user_avatar is None
