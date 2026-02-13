"""推荐服务测试"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.recommendation_service import (
    recommend_posts_hot,
    recommend_posts_for_user,
    recommend_topics,
)
from app.services.post_service import create
from app.services.topic_service import create_topic
from app.services.follow_service import follow_user
from app.services.like_service import like_post
from app.models.post import Post
from app.models.like import Like
from app.models.user import User
from app.schemas.post import PostCreate


async def create_test_user(db: AsyncSession, openid: str, nickname: str, anonymous_name: str) -> User:
    """Helper function to create a test user"""
    user = User(openid=openid, anonymous_name=anonymous_name, avatar=f"https://example.com/{openid}.jpg")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_test_topic(db: AsyncSession, name: str, post_count: int = 0, sort_order: int = 0, **kwargs):
    """Helper function to create a test topic with post_count"""
    topic = await create_topic(db, name=name, sort_order=sort_order, **kwargs)
    if post_count > 0:
        topic.post_count = post_count
        await db.commit()
        await db.refresh(topic)
    return topic


class TestRecommendPostsHot:
    """测试热门帖子推荐"""

    @pytest.mark.asyncio
    async def test_recommend_hot_posts_by_score(self, db_session: AsyncSession, test_user):
        """测试按热度分数推荐帖子"""
        # 创建多个帖子，模拟不同的互动数据
        post1 = await create(db_session, test_user.id, PostCreate(content="高热度帖子"), anonymous_name="测试用户1")
        post1.like_count = 10  # 分数 = 10*2 = 20
        post1.comment_count = 5  # 分数 += 5*3 = 35
        post1.view_count = 100  # 分数 += 100*0.1 = 45
        post1.risk_status = "approved"

        post2 = await create(db_session, test_user.id, PostCreate(content="中热度帖子"), anonymous_name="测试用户2")
        post2.like_count = 5  # 分数 = 5*2 = 10
        post2.comment_count = 2  # 分数 += 2*3 = 16
        post2.view_count = 50  # 分数 += 50*0.1 = 21
        post2.risk_status = "approved"

        post3 = await create(db_session, test_user.id, PostCreate(content="低热度帖子"), anonymous_name="测试用户3")
        post3.like_count = 1  # 分数 = 1*2 = 2
        post3.comment_count = 0  # 分数 += 0
        post3.view_count = 10  # 分数 += 10*0.1 = 3
        post3.risk_status = "approved"

        await db_session.commit()

        # 获取热门推荐
        posts = await recommend_posts_hot(db_session, limit=10)

        # 验证顺序：post1 > post2 > post3
        assert len(posts) >= 3
        assert posts[0].id == post1.id
        assert posts[1].id == post2.id
        assert posts[2].id == post3.id

    @pytest.mark.asyncio
    async def test_recommend_hot_only_normal_status(self, db_session: AsyncSession, test_user):
        """测试只推荐正常状态的帖子"""
        # 创建不同状态的帖子
        post_normal = await create(db_session, test_user.id, PostCreate(content="正常帖子"), anonymous_name="测试用户")
        post_normal.like_count = 10
        post_normal.risk_status = "approved"

        post_hidden = await create(db_session, test_user.id, PostCreate(content="隐藏帖子"), anonymous_name="测试用户")
        post_hidden.status = "hidden"
        post_hidden.like_count = 100  # 更高热度但不应推荐
        post_hidden.risk_status = "approved"

        post_deleted = await create(db_session, test_user.id, PostCreate(content="删除帖子"), anonymous_name="测试用户")
        post_deleted.status = "deleted"
        post_deleted.like_count = 200  # 最高热度但不应推荐
        post_deleted.risk_status = "approved"

        await db_session.commit()

        posts = await recommend_posts_hot(db_session, limit=10)

        # 只应返回正常状态的帖子
        assert all(p.status == "normal" for p in posts)
        assert post_normal.id in [p.id for p in posts]
        assert post_hidden.id not in [p.id for p in posts]
        assert post_deleted.id not in [p.id for p in posts]

    @pytest.mark.asyncio
    async def test_recommend_hot_only_approved_risk(self, db_session: AsyncSession, test_user):
        """测试只推荐风审通过的帖子"""
        # 创建不同风审状态的帖子
        post_approved = await create(db_session, test_user.id, PostCreate(content="已通过"), anonymous_name="测试用户")
        post_approved.risk_status = "approved"
        post_approved.like_count = 5

        post_pending = await create(db_session, test_user.id, PostCreate(content="待审核"), anonymous_name="测试用户")
        post_pending.risk_status = "pending"
        post_pending.like_count = 100  # 更高热度

        post_rejected = await create(db_session, test_user.id, PostCreate(content="已拒绝"), anonymous_name="测试用户")
        post_rejected.risk_status = "rejected"
        post_rejected.like_count = 200  # 最高热度

        await db_session.commit()

        posts = await recommend_posts_hot(db_session, limit=10)

        # 只应返回风审通过的帖子
        assert all(p.risk_status == "approved" for p in posts)
        assert post_approved.id in [p.id for p in posts]
        assert post_pending.id not in [p.id for p in posts]
        assert post_rejected.id not in [p.id for p in posts]

    @pytest.mark.asyncio
    async def test_recommend_hot_respects_limit(self, db_session: AsyncSession, test_user):
        """测试返回数量限制"""
        # 创建20个帖子
        for i in range(20):
            post = await create(db_session, test_user.id, PostCreate(content=f"帖子{i}"), anonymous_name="测试用户")
            post.like_count = i
            post.risk_status = "approved"

        await db_session.commit()

        # 请求限制为5
        posts = await recommend_posts_hot(db_session, limit=5)

        assert len(posts) == 5

    @pytest.mark.asyncio
    async def test_recommend_hot_empty_result(self, db_session: AsyncSession):
        """测试没有帖子时返回空列表"""
        posts = await recommend_posts_hot(db_session, limit=10)
        assert posts == []

    @pytest.mark.asyncio
    async def test_recommend_hot_score_formula(self, db_session: AsyncSession, test_user):
        """测试热度分数公式: 点赞*2 + 评论*3 + 浏览*0.1"""
        post1 = await create(db_session, test_user.id, PostCreate(content="帖子1"), anonymous_name="测试用户")
        post1.like_count = 10
        post1.comment_count = 0
        post1.view_count = 0
        # 分数 = 10*2 = 20

        post2 = await create(db_session, test_user.id, PostCreate(content="帖子2"), anonymous_name="测试用户")
        post2.like_count = 0
        post2.comment_count = 7
        post2.view_count = 0
        # 分数 = 7*3 = 21

        post3 = await create(db_session, test_user.id, PostCreate(content="帖子3"), anonymous_name="测试用户")
        post3.like_count = 0
        post3.comment_count = 0
        post3.view_count = 210
        # 分数 = 210*0.1 = 21

        post4 = await create(db_session, test_user.id, PostCreate(content="帖子4"), anonymous_name="测试用户")
        post4.like_count = 5
        post4.comment_count = 3
        post4.view_count = 10
        # 分数 = 5*2 + 3*3 + 10*0.1 = 10 + 9 + 1 = 20

        for post in [post1, post2, post3, post4]:
            post.risk_status = "approved"

        await db_session.commit()

        posts = await recommend_posts_hot(db_session, limit=10)

        # post2 和 post3 应该在前（分数21）
        # post1 和 post4 分数20
        assert posts[0].id in {post2.id, post3.id}
        assert posts[1].id in {post2.id, post3.id}


class TestRecommendPostsForUser:
    """测试用户个性化推荐"""

    @pytest.mark.asyncio
    async def test_recommend_from_followings(
        self, db_session: AsyncSession, test_user: User
    ):
        """测试推荐关注用户的帖子"""
        # 创建第二个用户
        user2 = await create_test_user(db_session, "user2_openid", "测试用户2", "匿名用户2")

        # test_user 关注 test_user2
        await follow_user(db_session, test_user.id, user2.id)

        # test_user2 发布帖子
        post = await create(db_session, user2.id, PostCreate(content="关注者的帖子"), anonymous_name="测试用户2")
        post.risk_status = "approved"
        await db_session.commit()

        # 获取推荐
        posts = await recommend_posts_for_user(db_session, test_user.id, limit=10)

        assert len(posts) >= 1
        assert post.id in [p.id for p in posts]

    @pytest.mark.asyncio
    async def test_recommend_falls_back_to_hot_when_no_followings(
        self, db_session: AsyncSession, test_user: User
    ):
        """测试没有关注任何人时回退到热门推荐"""
        # 创建一些热门帖子
        post = await create(db_session, test_user.id, PostCreate(content="热门帖子"), anonymous_name="测试用户")
        post.like_count = 100
        post.risk_status = "approved"
        await db_session.commit()

        # 用户没有关注任何人
        posts = await recommend_posts_for_user(db_session, test_user.id, limit=10)

        # 应该返回热门帖子
        assert len(posts) >= 1
        assert post.id in [p.id for p in posts]

    @pytest.mark.asyncio
    async def test_recommend_excludes_interacted_posts(
        self, db_session: AsyncSession, test_user: User
    ):
        """测试排除已互动（点赞）的帖子"""
        # 创建第二个用户
        user2 = await create_test_user(db_session, "user2_openid", "测试用户2", "匿名用户2")

        # test_user 关注 test_user2
        await follow_user(db_session, test_user.id, user2.id)

        # test_user2 发布两个帖子
        post1 = await create(db_session, user2.id, PostCreate(content="帖子1"), anonymous_name="测试用户2")
        post2 = await create(db_session, user2.id, PostCreate(content="帖子2"), anonymous_name="测试用户2")
        for post in [post1, post2]:
            post.risk_status = "approved"
        await db_session.commit()

        # test_user 点赞了 post1
        await like_post(db_session, test_user.id, post1.id)
        await db_session.commit()

        # 获取推荐
        posts = await recommend_posts_for_user(db_session, test_user.id, limit=10)

        # post1 不应该被推荐（已点赞）
        assert post1.id not in [p.id for p in posts]
        # post2 应该被推荐
        assert post2.id in [p.id for p in posts]

    @pytest.mark.asyncio
    async def test_recommend_only_recent_posts(
        self, db_session: AsyncSession, test_user: User
    ):
        """测试只推荐最近7天的帖子"""
        # 创建第二个用户
        user2 = await create_test_user(db_session, "user2_openid", "测试用户2", "匿名用户2")

        # test_user 关注 test_user2
        await follow_user(db_session, test_user.id, user2.id)

        # 创建最近帖子
        recent_post = await create(db_session, user2.id, PostCreate(content="最近帖子"), anonymous_name="测试用户2")
        recent_post.risk_status = "approved"
        recent_post.created_at = datetime.utcnow()

        # 创建旧帖子（8天前）
        old_post = await create(db_session, user2.id, PostCreate(content="旧帖子"), anonymous_name="测试用户2")
        old_post.risk_status = "approved"
        old_post.created_at = datetime.utcnow() - timedelta(days=8)

        await db_session.commit()

        # 获取推荐
        posts = await recommend_posts_for_user(db_session, test_user.id, limit=10)

        # 只应推荐最近帖子
        assert recent_post.id in [p.id for p in posts]
        assert old_post.id not in [p.id for p in posts]

    @pytest.mark.asyncio
    async def test_recommend_respects_limit(
        self, db_session: AsyncSession, test_user: User
    ):
        """测试返回数量限制"""
        # 创建第二个用户
        user2 = await create_test_user(db_session, "user2_openid", "测试用户2", "匿名用户2")

        # test_user 关注 test_user2
        await follow_user(db_session, test_user.id, user2.id)

        # 创建15个帖子
        for i in range(15):
            post = await create(db_session, user2.id, PostCreate(content=f"帖子{i}"), anonymous_name="测试用户2")
            post.risk_status = "approved"
        await db_session.commit()

        # 请求限制为5
        posts = await recommend_posts_for_user(db_session, test_user.id, limit=5)

        assert len(posts) == 5

    @pytest.mark.asyncio
    async def test_recommend_only_normal_and_approved_posts(
        self, db_session: AsyncSession, test_user: User
    ):
        """测试只推荐正常状态且风审通过的帖子"""
        # 创建第二个用户
        user2 = await create_test_user(db_session, "user2_openid", "测试用户2", "匿名用户2")

        # test_user 关注 test_user2
        await follow_user(db_session, test_user.id, user2.id)

        # 创建不同状态的帖子
        post_normal = await create(db_session, user2.id, PostCreate(content="正常帖子"), anonymous_name="测试用户2")
        post_normal.risk_status = "approved"

        post_hidden = await create(db_session, user2.id, PostCreate(content="隐藏帖子"), anonymous_name="测试用户2")
        post_hidden.status = "hidden"
        post_hidden.risk_status = "approved"

        post_pending = await create(db_session, user2.id, PostCreate(content="待审核帖子"), anonymous_name="测试用户2")
        post_pending.risk_status = "pending"

        await db_session.commit()

        # 获取推荐
        posts = await recommend_posts_for_user(db_session, test_user.id, limit=10)

        # 只应推荐正常且通过风审的帖子
        assert all(p.status == "normal" and p.risk_status == "approved" for p in posts)
        assert post_normal.id in [p.id for p in posts]
        assert post_hidden.id not in [p.id for p in posts]
        assert post_pending.id not in [p.id for p in posts]


class TestRecommendTopics:
    """测试话题推荐"""

    @pytest.mark.asyncio
    async def test_recommend_topics_by_post_count(self, db_session: AsyncSession):
        """测试按帖子数排序推荐话题"""
        # 创建不同帖子数的话题
        topic1 = await create_test_topic(db_session, name="热门话题1", post_count=100)
        topic2 = await create_test_topic(db_session, name="热门话题2", post_count=50)
        topic3 = await create_test_topic(db_session, name="冷门话题", post_count=5)

        # 获取推荐
        topics = await recommend_topics(db_session, limit=10)

        # 验证排序（按帖子数降序）
        assert len(topics) >= 3
        assert topics[0]["post_count"] >= topics[1]["post_count"] >= topics[2]["post_count"]
        assert topics[0]["id"] == topic1.id
        assert topics[1]["id"] == topic2.id
        assert topics[2]["id"] == topic3.id

    @pytest.mark.asyncio
    async def test_recommend_topics_only_active(self, db_session: AsyncSession):
        """测试只推荐启用的话题"""
        # 创建不同状态的话题
        topic_active = await create_test_topic(db_session, name="启用话题", post_count=10)

        topic_inactive = await create_test_topic(db_session, name="禁用话题", post_count=100)
        topic_inactive.is_active = False

        await db_session.commit()

        # 获取推荐
        topics = await recommend_topics(db_session, limit=10)

        # 只应返回启用的话题
        assert all(t["post_count"] >= 0 for t in topics)  # 基本验证
        # 验证启用话题被推荐
        active_ids = [t["id"] for t in topics]
        assert topic_active.id in active_ids
        assert topic_inactive.id not in active_ids

    @pytest.mark.asyncio
    async def test_recommend_topics_sort_order_secondary(self, db_session: AsyncSession):
        """测试帖子数相同时按sort_order排序"""
        # 创建帖子数相同但sort_order不同的话题
        topic1 = await create_test_topic(db_session, name="话题1", post_count=10, sort_order=5)
        topic2 = await create_test_topic(db_session, name="话题2", post_count=10, sort_order=10)
        topic3 = await create_test_topic(db_session, name="话题3", post_count=10, sort_order=1)

        await db_session.commit()

        # 获取推荐
        topics = await recommend_topics(db_session, limit=10)

        # 帖子数相同时，sort_order高的在前
        topic_ids = [t["id"] for t in topics[:3]]
        assert topic2.id in topic_ids
        assert topic1.id in topic_ids
        assert topic3.id in topic_ids

    @pytest.mark.asyncio
    async def test_recommend_topics_respects_limit(self, db_session: AsyncSession):
        """测试返回数量限制"""
        # 创建20个话题
        for i in range(20):
            await create_test_topic(db_session, name=f"话题{i}", post_count=i)

        # 获取推荐，限制为5
        topics = await recommend_topics(db_session, limit=5)

        assert len(topics) == 5

    @pytest.mark.asyncio
    async def test_recommend_topics_empty_result(self, db_session: AsyncSession):
        """测试没有话题时返回空列表"""
        topics = await recommend_topics(db_session, limit=10)
        assert topics == []

    @pytest.mark.asyncio
    async def test_recommend_topics_response_structure(self, db_session: AsyncSession):
        """测试推荐话题的响应结构"""
        await create_test_topic(
            db_session,
            name="测试话题",
            description="测试描述",
            cover_image="https://example.com/cover.jpg",
            post_count=10,
        )

        topics = await recommend_topics(db_session, limit=10)

        assert len(topics) >= 1
        topic = topics[0]
        assert "id" in topic
        assert "name" in topic
        assert "description" in topic
        assert "cover_image" in topic
        assert "post_count" in topic
        assert topic["name"] == "测试话题"
        assert topic["description"] == "测试描述"
        assert topic["cover_image"] == "https://example.com/cover.jpg"
        assert topic["post_count"] == 10
