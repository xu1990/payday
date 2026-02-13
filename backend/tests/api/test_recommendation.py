"""推荐接口API测试"""
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.post_service import create
from app.services.topic_service import create_topic
from app.schemas.post import PostCreate


async def create_test_user(db: AsyncSession, openid: str, anonymous_name: str) -> User:
    """Helper function to create a test user"""
    user = User(openid=openid, anonymous_name=anonymous_name, avatar=f"https://example.com/{openid}.jpg")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_test_topic(db: AsyncSession, name: str, post_count: int = 0, **kwargs):
    """Helper function to create a test topic with post_count"""
    topic = await create_topic(db, name=name, **kwargs)
    if post_count > 0:
        topic.post_count = post_count
        await db.commit()
        await db.refresh(topic)
    return topic


@pytest.mark.asyncio
class TestGetHotPostsEndpoint:
    """测试获取热门帖子接口"""

    async def test_get_hot_posts(self, client, db_session: AsyncSession):
        """测试获取热门帖子"""
        # 创建用户和帖子
        user = await create_test_user(db_session, "test_openid", "测试用户")
        post = await create(db_session, user.id, PostCreate(content="热门帖子"), anonymous_name="测试用户")
        post.like_count = 100
        post.risk_status = "approved"
        await db_session.commit()

        response = client.get("/api/v1/recommendations/hot")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_hot_posts_with_limit(self, client, db_session: AsyncSession):
        """测试限制返回数量"""
        user = await create_test_user(db_session, "test_openid", "测试用户")
        for i in range(5):
            post = await create(db_session, user.id, PostCreate(content=f"帖子{i}"), anonymous_name="测试用户")
            post.like_count = i
            post.risk_status = "approved"
        await db_session.commit()

        response = client.get("/api/v1/recommendations/hot?limit=3")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    async def test_get_hot_posts_limit_validation(self, client):
        """测试limit参数验证"""
        # 超过最大值
        response = client.get("/api/v1/recommendations/hot?limit=100")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 小于最小值
        response = client.get("/api/v1/recommendations/hot?limit=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_hot_posts_empty(self, client):
        """测试没有帖子时返回空列表"""
        response = client.get("/api/v1/recommendations/hot")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []


@pytest.mark.asyncio
class TestGetPersonalizedFeedEndpoint:
    """测试获取个性化推荐接口"""

    async def test_get_personalized_feed(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试获取个性化推荐"""
        # 创建热门帖子（回退场景）
        post = await create(db_session, test_user.id, PostCreate(content="热门帖子"), anonymous_name="测试用户")
        post.like_count = 100
        post.risk_status = "approved"
        await db_session.commit()

        response = client.get("/api/v1/recommendations/feed", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_personalized_feed_from_followings(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试从关注用户获取推荐"""
        # 创建第二个用户
        user2 = await create_test_user(db_session, "user2_openid", "测试用户2")

        # test_user 关注 user2
        from app.services.follow_service import follow_user
        await follow_user(db_session, test_user.id, user2.id)

        # user2 发布帖子
        post = await create(db_session, user2.id, PostCreate(content="关注者的帖子"), anonymous_name="测试用户2")
        post.risk_status = "approved"
        await db_session.commit()

        response = client.get("/api/v1/recommendations/feed", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # 应该包含关注者的帖子
        assert any(p["id"] == post.id for p in data)

    async def test_get_personalized_feed_with_limit(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试限制返回数量"""
        # 创建多个帖子
        for i in range(5):
            post = await create(db_session, test_user.id, PostCreate(content=f"帖子{i}"), anonymous_name="测试用户")
            post.like_count = i
            post.risk_status = "approved"
        await db_session.commit()

        response = client.get("/api/v1/recommendations/feed?limit=3", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    async def test_get_personalized_feed_requires_auth(self, client):
        """测试需要认证"""
        response = client.get("/api/v1/recommendations/feed")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_personalized_feed_limit_validation(self, client, test_user: User, user_headers: dict):
        """测试limit参数验证"""
        # 超过最大值
        response = client.get("/api/v1/recommendations/feed?limit=100", headers=user_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 小于最小值
        response = client.get("/api/v1/recommendations/feed?limit=0", headers=user_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestGetRecommendedTopicsEndpoint:
    """测试获取推荐话题接口"""

    async def test_get_recommended_topics(self, client, db_session: AsyncSession):
        """测试获取推荐话题"""
        # 创建话题
        await create_test_topic(db_session, name="热门话题", post_count=100)
        await db_session.commit()

        response = client.get("/api/v1/recommendations/topics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) >= 1

    async def test_get_recommended_topics_sorted_by_post_count(self, client, db_session: AsyncSession):
        """测试按帖子数排序"""
        # 创建不同帖子数的话题
        await create_test_topic(db_session, name="热门话题1", post_count=100)
        await create_test_topic(db_session, name="热门话题2", post_count=50)
        await create_test_topic(db_session, name="冷门话题", post_count=5)
        await db_session.commit()

        response = client.get("/api/v1/recommendations/topics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        items = data["items"]
        # 验证按帖子数降序
        assert items[0]["post_count"] >= items[1]["post_count"] >= items[2]["post_count"]

    async def test_get_recommended_topics_only_active(self, client, db_session: AsyncSession):
        """测试只返回启用的话题"""
        # 创建启用和禁用的话题
        topic_active = await create_test_topic(db_session, name="启用话题", post_count=10)

        topic_inactive = await create_test_topic(db_session, name="禁用话题", post_count=100)
        topic_inactive.is_active = False
        await db_session.commit()

        response = client.get("/api/v1/recommendations/topics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        items = data["items"]
        # 只应返回启用的话题
        assert any(t["id"] == topic_active.id for t in items)
        assert not any(t["id"] == topic_inactive.id for t in items)

    async def test_get_recommended_topics_with_limit(self, client, db_session: AsyncSession):
        """测试限制返回数量"""
        # 创建20个话题
        for i in range(20):
            await create_test_topic(db_session, name=f"话题{i}", post_count=i)
        await db_session.commit()

        response = client.get("/api/v1/recommendations/topics?limit=5")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 5

    async def test_get_recommended_topics_empty(self, client):
        """测试没有话题时返回空列表"""
        response = client.get("/api/v1/recommendations/topics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []

    async def test_get_recommended_topics_response_structure(self, client, db_session: AsyncSession):
        """测试响应结构"""
        await create_test_topic(
            db_session,
            name="测试话题",
            description="测试描述",
            cover_image="https://example.com/cover.jpg",
            post_count=10,
        )
        await db_session.commit()

        response = client.get("/api/v1/recommendations/topics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        items = data["items"]
        assert len(items) >= 1

        topic = items[0]
        assert "id" in topic
        assert "name" in topic
        assert "description" in topic
        assert "cover_image" in topic
        assert "post_count" in topic
        assert topic["name"] == "测试话题"
        assert topic["description"] == "测试描述"
        assert topic["cover_image"] == "https://example.com/cover.jpg"
        assert topic["post_count"] == 10

    async def test_get_recommended_topics_limit_validation(self, client):
        """测试limit参数验证"""
        # 超过最大值
        response = client.get("/api/v1/recommendations/topics?limit=100")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # 小于最小值
        response = client.get("/api/v1/recommendations/topics?limit=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
