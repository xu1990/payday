import pytest
from app.models.post import Post


@pytest.mark.asyncio
async def test_post_work_type_enum(db_session):
    """Test that posts can have type='work'"""
    post = Post(
        id="test-post-work",
        user_id="test-user-1",
        anonymous_name="测试用户",
        type="work",  # New work type
        content="加班记录"
    )
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    assert post.type == "work"
