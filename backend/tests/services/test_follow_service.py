"""关注服务集成测试"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import follow_service
from app.models.follow import Follow
from app.models.post import Post
from tests.test_utils import TestDataFactory


class TestFollowUser:
    """测试关注用户功能"""

    @pytest.mark.asyncio
    async def test_follow_user_success(self, db_session: AsyncSession):
        """测试成功关注用户"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        result = await follow_service.follow_user(db_session, user1.id, user2.id)

        # 验证关注成功
        assert result is True

        # 验证关注关系已创建
        is_following = await follow_service.is_following(db_session, user1.id, user2.id)
        assert is_following is True

    @pytest.mark.asyncio
    async def test_follow_user_increments_counts(self, db_session: AsyncSession):
        """测试关注增加用户计数"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        initial_follower_count = user2.follower_count or 0
        initial_following_count = user1.following_count or 0

        await follow_service.follow_user(db_session, user1.id, user2.id)

        # 刷新并验证计数增加
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        assert user2.follower_count == initial_follower_count + 1
        assert user1.following_count == initial_following_count + 1

    @pytest.mark.asyncio
    async def test_follow_user_idempotent(self, db_session: AsyncSession):
        """测试重复关注幂等性"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 第一次关注
        result1 = await follow_service.follow_user(db_session, user1.id, user2.id)
        assert result1 is True

        # 第二次关注（幂等）
        result2 = await follow_service.follow_user(db_session, user1.id, user2.id)
        assert result2 is False

        # 验证计数只增加一次
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        assert user1.following_count == 1
        assert user2.follower_count == 1

    @pytest.mark.asyncio
    async def test_follow_self_returns_false(self, db_session: AsyncSession):
        """测试不能关注自己"""
        user1 = await TestDataFactory.create_user(db_session, "user1")

        result = await follow_service.follow_user(db_session, user1.id, user1.id)

        # 验证返回 False
        assert result is False

        # 验证没有创建关注关系
        is_following = await follow_service.is_following(db_session, user1.id, user1.id)
        assert is_following is False

    @pytest.mark.asyncio
    async def test_follow_nonexistent_user(self, db_session: AsyncSession):
        """测试关注不存在的用户"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        nonexistent_user_id = "nonexistent_user_id"

        # 关注不存在的用户 - 会创建记录但用户计数不会更新
        result = await follow_service.follow_user(db_session, user1.id, nonexistent_user_id)

        # Follow关系会创建成功
        assert result is True

        # 验证关注关系存在
        is_following = await follow_service.is_following(db_session, user1.id, nonexistent_user_id)
        assert is_following is True


class TestUnfollowUser:
    """测试取消关注功能"""

    @pytest.mark.asyncio
    async def test_unfollow_user_success(self, db_session: AsyncSession):
        """测试成功取消关注"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 先关注
        await follow_service.follow_user(db_session, user1.id, user2.id)

        # 取消关注
        result = await follow_service.unfollow_user(db_session, user1.id, user2.id)

        assert result is True

        # 验证关注关系已删除
        is_following = await follow_service.is_following(db_session, user1.id, user2.id)
        assert is_following is False

    @pytest.mark.asyncio
    async def test_unfollow_user_decrements_counts(self, db_session: AsyncSession):
        """测试取消关注减少用户计数"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 先关注
        await follow_service.follow_user(db_session, user1.id, user2.id)
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        initial_follower_count = user2.follower_count
        initial_following_count = user1.following_count

        # 取消关注
        await follow_service.unfollow_user(db_session, user1.id, user2.id)

        # 刷新并验证计数减少
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        assert user2.follower_count == initial_follower_count - 1
        assert user1.following_count == initial_following_count - 1

    @pytest.mark.asyncio
    async def test_unfollow_user_not_following(self, db_session: AsyncSession):
        """测试取消未关注的用户"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 取消未关注的用户
        result = await follow_service.unfollow_user(db_session, user1.id, user2.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_unfollow_user_count_never_negative(self, db_session: AsyncSession):
        """测试关注计数不会变成负数"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 先关注
        await follow_service.follow_user(db_session, user1.id, user2.id)

        # 手动将计数设为0
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        user1.following_count = 0
        user2.follower_count = 0
        await db_session.commit()

        # 取消关注
        await follow_service.unfollow_user(db_session, user1.id, user2.id)

        # 刷新并验证计数不为负
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        assert user1.following_count == 0
        assert user2.follower_count == 0


class TestGetFollowers:
    """测试获取粉丝列表功能"""

    @pytest.mark.asyncio
    async def test_get_followers_empty(self, db_session: AsyncSession):
        """测试获取空粉丝列表"""
        user = await TestDataFactory.create_user(db_session, "user1")

        followers, total = await follow_service.get_followers(db_session, user.id)

        assert followers == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_followers_single(self, db_session: AsyncSession):
        """测试获取单个粉丝"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        await follow_service.follow_user(db_session, user2.id, user1.id)

        followers, total = await follow_service.get_followers(db_session, user1.id)

        assert len(followers) == 1
        assert total == 1
        assert followers[0].id == user2.id

    @pytest.mark.asyncio
    async def test_get_followers_multiple(self, db_session: AsyncSession):
        """测试获取多个粉丝"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        user3 = await TestDataFactory.create_user(db_session, "user3")
        user4 = await TestDataFactory.create_user(db_session, "user4")

        # user2, user3, user4 都关注 user1
        await follow_service.follow_user(db_session, user2.id, user1.id)
        await follow_service.follow_user(db_session, user3.id, user1.id)
        await follow_service.follow_user(db_session, user4.id, user1.id)

        followers, total = await follow_service.get_followers(db_session, user1.id)

        assert len(followers) == 3
        assert total == 3
        follower_ids = [f.id for f in followers]
        assert user2.id in follower_ids
        assert user3.id in follower_ids
        assert user4.id in follower_ids

    @pytest.mark.asyncio
    async def test_get_followers_with_pagination(self, db_session: AsyncSession):
        """测试粉丝列表分页"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        users = []
        for i in range(5):
            user = await TestDataFactory.create_user(db_session, f"user{i+2}")
            users.append(user)
            await follow_service.follow_user(db_session, user.id, user1.id)

        # 第一页：3个
        followers1, total1 = await follow_service.get_followers(db_session, user1.id, limit=3, offset=0)
        assert len(followers1) == 3
        assert total1 == 5

        # 第二页：2个
        followers2, total2 = await follow_service.get_followers(db_session, user1.id, limit=3, offset=3)
        assert len(followers2) == 2
        assert total2 == 5

        # 验证没有重复
        ids1 = [f.id for f in followers1]
        ids2 = [f.id for f in followers2]
        assert set(ids1).isdisjoint(set(ids2))

    @pytest.mark.asyncio
    async def test_get_followers_ordered_by_created_at(self, db_session: AsyncSession):
        """测试粉丝列表按关注时间倒序排列"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        user3 = await TestDataFactory.create_user(db_session, "user3")

        # 按顺序关注
        await follow_service.follow_user(db_session, user2.id, user1.id)
        await follow_service.follow_user(db_session, user3.id, user1.id)

        followers, total = await follow_service.get_followers(db_session, user1.id)

        # user3 应该在前面（后关注的在前）
        assert len(followers) == 2
        assert followers[0].id == user3.id
        assert followers[1].id == user2.id


class TestGetFollowing:
    """测试获取关注列表功能"""

    @pytest.mark.asyncio
    async def test_get_following_empty(self, db_session: AsyncSession):
        """测试获取空关注列表"""
        user = await TestDataFactory.create_user(db_session, "user1")

        following, total = await follow_service.get_following(db_session, user.id)

        assert following == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_following_single(self, db_session: AsyncSession):
        """测试获取单个关注"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        await follow_service.follow_user(db_session, user1.id, user2.id)

        following, total = await follow_service.get_following(db_session, user1.id)

        assert len(following) == 1
        assert total == 1
        assert following[0].id == user2.id

    @pytest.mark.asyncio
    async def test_get_following_multiple(self, db_session: AsyncSession):
        """测试获取多个关注"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        user3 = await TestDataFactory.create_user(db_session, "user3")
        user4 = await TestDataFactory.create_user(db_session, "user4")

        # user1 关注 user2, user3, user4
        await follow_service.follow_user(db_session, user1.id, user2.id)
        await follow_service.follow_user(db_session, user1.id, user3.id)
        await follow_service.follow_user(db_session, user1.id, user4.id)

        following, total = await follow_service.get_following(db_session, user1.id)

        assert len(following) == 3
        assert total == 3
        following_ids = [f.id for f in following]
        assert user2.id in following_ids
        assert user3.id in following_ids
        assert user4.id in following_ids

    @pytest.mark.asyncio
    async def test_get_following_with_pagination(self, db_session: AsyncSession):
        """测试关注列表分页"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        users = []
        for i in range(5):
            user = await TestDataFactory.create_user(db_session, f"user{i+2}")
            users.append(user)
            await follow_service.follow_user(db_session, user1.id, user.id)

        # 第一页：3个
        following1, total1 = await follow_service.get_following(db_session, user1.id, limit=3, offset=0)
        assert len(following1) == 3
        assert total1 == 5

        # 第二页：2个
        following2, total2 = await follow_service.get_following(db_session, user1.id, limit=3, offset=3)
        assert len(following2) == 2
        assert total2 == 5

        # 验证没有重复
        ids1 = [f.id for f in following1]
        ids2 = [f.id for f in following2]
        assert set(ids1).isdisjoint(set(ids2))

    @pytest.mark.asyncio
    async def test_get_following_ordered_by_created_at(self, db_session: AsyncSession):
        """测试关注列表按关注时间倒序排列"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        user3 = await TestDataFactory.create_user(db_session, "user3")

        # 按顺序关注
        await follow_service.follow_user(db_session, user1.id, user2.id)
        await follow_service.follow_user(db_session, user1.id, user3.id)

        following, total = await follow_service.get_following(db_session, user1.id)

        # user3 应该在前面（后关注的在前）
        assert len(following) == 2
        assert following[0].id == user3.id
        assert following[1].id == user2.id


class TestIsFollowing:
    """测试检查是否关注功能"""

    @pytest.mark.asyncio
    async def test_is_following_true(self, db_session: AsyncSession):
        """测试检查关注状态 - 已关注"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        await follow_service.follow_user(db_session, user1.id, user2.id)

        is_following = await follow_service.is_following(db_session, user1.id, user2.id)

        assert is_following is True

    @pytest.mark.asyncio
    async def test_is_following_false(self, db_session: AsyncSession):
        """测试检查关注状态 - 未关注"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        is_following = await follow_service.is_following(db_session, user1.id, user2.id)

        assert is_following is False

    @pytest.mark.asyncio
    async def test_is_following_after_unfollow(self, db_session: AsyncSession):
        """测试取消关注后检查状态"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 关注
        await follow_service.follow_user(db_session, user1.id, user2.id)
        assert await follow_service.is_following(db_session, user1.id, user2.id) is True

        # 取消关注
        await follow_service.unfollow_user(db_session, user1.id, user2.id)
        assert await follow_service.is_following(db_session, user1.id, user2.id) is False


class TestFollowingPosts:
    """测试关注流功能"""

    @pytest.mark.asyncio
    async def test_count_following_posts_empty(self, db_session: AsyncSession):
        """测试关注流计数为空"""
        user = await TestDataFactory.create_user(db_session, "user1")

        count = await follow_service.count_following_posts(db_session, user.id)

        assert count == 0

    @pytest.mark.asyncio
    async def test_count_following_posts_single(self, db_session: AsyncSession):
        """测试关注流计数单个帖子"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # user1 关注 user2
        await follow_service.follow_user(db_session, user1.id, user2.id)

        # user2 发布帖子并设置为已审核通过
        post = await TestDataFactory.create_post(db_session, user2.id, content="测试帖子")
        post.risk_status = "approved"
        await db_session.commit()

        count = await follow_service.count_following_posts(db_session, user1.id)

        assert count == 1

    @pytest.mark.asyncio
    async def test_count_following_posts_multiple(self, db_session: AsyncSession):
        """测试关注流计数多个帖子"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        user3 = await TestDataFactory.create_user(db_session, "user3")

        # user1 关注 user2 和 user3
        await follow_service.follow_user(db_session, user1.id, user2.id)
        await follow_service.follow_user(db_session, user1.id, user3.id)

        # user2 发布2个帖子
        post1 = await TestDataFactory.create_post(db_session, user2.id, content="帖子1")
        post1.risk_status = "approved"
        post2 = await TestDataFactory.create_post(db_session, user2.id, content="帖子2")
        post2.risk_status = "approved"

        # user3 发布1个帖子
        post3 = await TestDataFactory.create_post(db_session, user3.id, content="帖子3")
        post3.risk_status = "approved"
        await db_session.commit()

        count = await follow_service.count_following_posts(db_session, user1.id)

        assert count == 3

    @pytest.mark.asyncio
    async def test_count_following_posts_excludes_non_approved(self, db_session: AsyncSession):
        """测试关注流只包含已审核通过的帖子"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        await follow_service.follow_user(db_session, user1.id, user2.id)

        # user2 发布不同状态的帖子
        post1 = await TestDataFactory.create_post(db_session, user2.id, content="已审核")
        post1.risk_status = "approved"
        post2 = await TestDataFactory.create_post(db_session, user2.id, content="待审核")  # 默认pending
        post3 = await TestDataFactory.create_post(db_session, user2.id, content="已拒绝")
        post3.risk_status = "rejected"
        await db_session.commit()

        count = await follow_service.count_following_posts(db_session, user1.id)

        # 只计算已审核通过的
        assert count == 1

    @pytest.mark.asyncio
    async def test_count_following_posts_excludes_non_normal(self, db_session: AsyncSession):
        """测试关注流只包含正常状态的帖子"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        await follow_service.follow_user(db_session, user1.id, user2.id)

        # user2 发布不同状态的帖子
        post1 = await TestDataFactory.create_post(db_session, user2.id, content="正常")
        post1.risk_status = "approved"
        post2 = await TestDataFactory.create_post(db_session, user2.id, content="隐藏")
        post2.risk_status = "approved"
        post2.status = "hidden"
        post3 = await TestDataFactory.create_post(db_session, user2.id, content="删除")
        post3.risk_status = "approved"
        post3.status = "deleted"
        await db_session.commit()

        count = await follow_service.count_following_posts(db_session, user1.id)

        # 只计算正常状态的
        assert count == 1

    @pytest.mark.asyncio
    async def test_list_following_posts_empty(self, db_session: AsyncSession):
        """测试关注流列表为空"""
        user = await TestDataFactory.create_user(db_session, "user1")

        posts = await follow_service.list_following_posts(db_session, user.id)

        assert posts == []

    @pytest.mark.asyncio
    async def test_list_following_posts_single(self, db_session: AsyncSession):
        """测试关注流列表单个帖子"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        await follow_service.follow_user(db_session, user1.id, user2.id)
        post = await TestDataFactory.create_post(db_session, user2.id, content="测试帖子")
        post.risk_status = "approved"
        await db_session.commit()

        posts = await follow_service.list_following_posts(db_session, user1.id)

        assert len(posts) == 1
        assert posts[0].id == post.id
        assert posts[0].content == "测试帖子"

    @pytest.mark.asyncio
    async def test_list_following_posts_ordered_by_created_at(self, db_session: AsyncSession):
        """测试关注流按创建时间倒序排列"""
        import time
        from datetime import datetime, timedelta

        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        await follow_service.follow_user(db_session, user1.id, user2.id)

        # 发布多个帖子，手动设置不同的created_at时间
        now = datetime.utcnow()

        post1 = await TestDataFactory.create_post(db_session, user2.id, content="帖子1")
        post1.risk_status = "approved"
        post1.created_at = now
        await db_session.commit()

        time.sleep(0.01)  # 小延迟确保时间戳不同

        post2 = await TestDataFactory.create_post(db_session, user2.id, content="帖子2")
        post2.risk_status = "approved"
        post2.created_at = now + timedelta(seconds=1)
        await db_session.commit()

        time.sleep(0.01)

        post3 = await TestDataFactory.create_post(db_session, user2.id, content="帖子3")
        post3.risk_status = "approved"
        post3.created_at = now + timedelta(seconds=2)
        await db_session.commit()

        posts = await follow_service.list_following_posts(db_session, user1.id)

        # 验证倒序排列（最新的在前）
        assert len(posts) == 3
        assert posts[0].id == post3.id
        assert posts[1].id == post2.id
        assert posts[2].id == post1.id

    @pytest.mark.asyncio
    async def test_list_following_posts_with_pagination(self, db_session: AsyncSession):
        """测试关注流分页"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        await follow_service.follow_user(db_session, user1.id, user2.id)

        # 发布5个帖子
        for i in range(5):
            post = await TestDataFactory.create_post(db_session, user2.id, content=f"帖子{i+1}")
            post.risk_status = "approved"
        await db_session.commit()

        # 第一页：3个
        posts1 = await follow_service.list_following_posts(db_session, user1.id, limit=3, offset=0)
        assert len(posts1) == 3

        # 第二页：2个
        posts2 = await follow_service.list_following_posts(db_session, user1.id, limit=3, offset=3)
        assert len(posts2) == 2

        # 验证没有重复
        ids1 = [p.id for p in posts1]
        ids2 = [p.id for p in posts2]
        assert set(ids1).isdisjoint(set(ids2))

    @pytest.mark.asyncio
    async def test_list_following_posts_from_multiple_users(self, db_session: AsyncSession):
        """测试关注流包含多个关注用户的帖子"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        user3 = await TestDataFactory.create_user(db_session, "user3")

        await follow_service.follow_user(db_session, user1.id, user2.id)
        await follow_service.follow_user(db_session, user1.id, user3.id)

        # user2 发布2个帖子
        post1 = await TestDataFactory.create_post(db_session, user2.id, content="user2帖子1")
        post1.risk_status = "approved"
        post2 = await TestDataFactory.create_post(db_session, user2.id, content="user2帖子2")
        post2.risk_status = "approved"

        # user3 发布1个帖子
        post3 = await TestDataFactory.create_post(db_session, user3.id, content="user3帖子1")
        post3.risk_status = "approved"
        await db_session.commit()

        posts = await follow_service.list_following_posts(db_session, user1.id)

        assert len(posts) == 3
        post_ids = [p.id for p in posts]
        assert post1.id in post_ids
        assert post2.id in post_ids
        assert post3.id in post_ids

    @pytest.mark.asyncio
    async def test_list_following_posts_excludes_unfollowed_users(self, db_session: AsyncSession):
        """测试关注流不包含未关注用户的帖子"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        user3 = await TestDataFactory.create_user(db_session, "user3")

        # 只关注 user2
        await follow_service.follow_user(db_session, user1.id, user2.id)

        # user2 发布帖子
        post1 = await TestDataFactory.create_post(db_session, user2.id, content="user2帖子")
        post1.risk_status = "approved"

        # user3 也发布帖子（但user1没有关注user3）
        post2 = await TestDataFactory.create_post(db_session, user3.id, content="user3帖子")
        post2.risk_status = "approved"
        await db_session.commit()

        posts = await follow_service.list_following_posts(db_session, user1.id)

        # 只应该包含 user2 的帖子
        assert len(posts) == 1
        assert posts[0].user_id == user2.id


class TestFollowUnfollowFlow:
    """测试关注/取消关注的完整流程"""

    @pytest.mark.asyncio
    async def test_follow_unfollow_follow_flow(self, db_session: AsyncSession):
        """测试关注->取消->再关注的完整流程"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 关注
        result1 = await follow_service.follow_user(db_session, user1.id, user2.id)
        assert result1 is True
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        assert user1.following_count == 1
        assert user2.follower_count == 1

        # 取消关注
        result2 = await follow_service.unfollow_user(db_session, user1.id, user2.id)
        assert result2 is True
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        assert user1.following_count == 0
        assert user2.follower_count == 0

        # 再次关注
        result3 = await follow_service.follow_user(db_session, user1.id, user2.id)
        assert result3 is True
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        assert user1.following_count == 1
        assert user2.follower_count == 1

    @pytest.mark.asyncio
    async def test_multiple_users_follow_same_user(self, db_session: AsyncSession):
        """测试多个用户关注同一个用户"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        user3 = await TestDataFactory.create_user(db_session, "user3")
        user4 = await TestDataFactory.create_user(db_session, "user4")

        # user2, user3, user4 都关注 user1
        await follow_service.follow_user(db_session, user2.id, user1.id)
        await follow_service.follow_user(db_session, user3.id, user1.id)
        await follow_service.follow_user(db_session, user4.id, user1.id)

        # 验证 user1 的粉丝数
        await db_session.refresh(user1)
        assert user1.follower_count == 3

        # 验证粉丝列表
        followers, total = await follow_service.get_followers(db_session, user1.id)
        assert total == 3
        assert len(followers) == 3

    @pytest.mark.asyncio
    async def test_user_follows_multiple_users(self, db_session: AsyncSession):
        """测试一个用户关注多个用户"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        user3 = await TestDataFactory.create_user(db_session, "user3")
        user4 = await TestDataFactory.create_user(db_session, "user4")

        # user1 关注 user2, user3, user4
        await follow_service.follow_user(db_session, user1.id, user2.id)
        await follow_service.follow_user(db_session, user1.id, user3.id)
        await follow_service.follow_user(db_session, user1.id, user4.id)

        # 验证 user1 的关注数
        await db_session.refresh(user1)
        assert user1.following_count == 3

        # 验证关注列表
        following, total = await follow_service.get_following(db_session, user1.id)
        assert total == 3
        assert len(following) == 3

    @pytest.mark.asyncio
    async def test_bidirectional_follow(self, db_session: AsyncSession):
        """测试双向关注（互关）"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # user1 关注 user2
        await follow_service.follow_user(db_session, user1.id, user2.id)
        # user2 也关注 user1
        await follow_service.follow_user(db_session, user2.id, user1.id)

        # 验证双方的关注和粉丝数
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        assert user1.following_count == 1  # user1 关注了 user2
        assert user1.follower_count == 1  # user1 被 user2 关注
        assert user2.following_count == 1  # user2 关注了 user1
        assert user2.follower_count == 1  # user2 被 user1 关注

        # 验证双方都有关注关系
        assert await follow_service.is_following(db_session, user1.id, user2.id) is True
        assert await follow_service.is_following(db_session, user2.id, user1.id) is True
