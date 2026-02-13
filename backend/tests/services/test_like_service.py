"""点赞服务集成测试"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import like_service
from app.models.like import Like
from tests.test_utils import TestDataFactory


class TestLikePost:
    """测试帖子点赞功能"""

    @pytest.mark.asyncio
    async def test_like_post_success(self, db_session: AsyncSession):
        """测试成功点赞帖子"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            like, created = await like_service.like_post(db_session, user.id, post.id)

            # 验证点赞记录创建成功
            assert like is not None
            assert like.id is not None
            assert like.user_id == user.id
            assert like.target_type == "post"
            assert like.target_id == post.id
            assert created is True

    @pytest.mark.asyncio
    async def test_like_post_increments_count(self, db_session: AsyncSession):
        """测试点赞增加帖子计数"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        initial_count = post.like_count or 0

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            await like_service.like_post(db_session, user.id, post.id)

            # 刷新并验证计数增加
            await db_session.refresh(post)
            assert post.like_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_like_post_idempotent(self, db_session: AsyncSession):
        """测试重复点赞幂等性"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 第一次点赞
            like1, created1 = await like_service.like_post(db_session, user.id, post.id)
            assert created1 is True

            # 第二次点赞（幂等）
            like2, created2 = await like_service.like_post(db_session, user.id, post.id)
            assert created2 is False
            assert like2.id == like1.id

            # 验证计数只增加一次
            await db_session.refresh(post)
            assert post.like_count == 1

    @pytest.mark.asyncio
    async def test_like_post_sends_notification_to_author(self, db_session: AsyncSession):
        """测试点赞通知帖子作者"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user1.id)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock) as mock_notify:
            await like_service.like_post(db_session, user2.id, post.id)

            # 验证发送了通知 (db_session, user_id, type, title, content, related_id)
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args[0]
            assert call_args[0] == db_session
            assert str(call_args[1]) == str(user1.id)
            assert call_args[2] == "like"
            assert call_args[3] == "新点赞"

    @pytest.mark.asyncio
    async def test_like_own_post_no_notification(self, db_session: AsyncSession):
        """测试自己点赞自己的帖子不发送通知"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock) as mock_notify:
            await like_service.like_post(db_session, user.id, post.id)

            # 验证没有发送通知
            mock_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_like_post_nonexistent_post(self, db_session: AsyncSession):
        """测试点赞不存在的帖子"""
        user = await TestDataFactory.create_user(db_session)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 点赞不存在的帖子应该仍然创建点赞记录
            like, created = await like_service.like_post(db_session, user.id, "nonexistent_post_id")

            # 点赞记录仍然会创建成功，即使帖子不存在
            assert like is not None
            assert created is True


class TestUnlikePost:
    """测试帖子取消点赞功能"""

    @pytest.mark.asyncio
    async def test_unlike_post_success(self, db_session: AsyncSession):
        """测试成功取消点赞"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 先点赞
            await like_service.like_post(db_session, user.id, post.id)

            # 取消点赞
            result = await like_service.unlike_post(db_session, user.id, post.id)

            assert result is True

            # 验证点赞记录已被删除
            like = await like_service._get_like(db_session, user.id, "post", post.id)
            assert like is None

    @pytest.mark.asyncio
    async def test_unlike_post_decrements_count(self, db_session: AsyncSession):
        """测试取消点赞减少帖子计数"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 先点赞
            await like_service.like_post(db_session, user.id, post.id)
            await db_session.refresh(post)
            initial_count = post.like_count

            # 取消点赞
            await like_service.unlike_post(db_session, user.id, post.id)

            # 刷新并验证计数减少
            await db_session.refresh(post)
            assert post.like_count == max(0, initial_count - 1)

    @pytest.mark.asyncio
    async def test_unlike_post_not_liked(self, db_session: AsyncSession):
        """测试取消未点赞的帖子"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 取消未点赞的帖子
        result = await like_service.unlike_post(db_session, user.id, post.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_unlike_post_count_never_negative(self, db_session: AsyncSession):
        """测试点赞计数不会变成负数"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 先点赞
            await like_service.like_post(db_session, user.id, post.id)

            # 手动将计数设为0
            post.like_count = 0
            await db_session.commit()

            # 取消点赞
            await like_service.unlike_post(db_session, user.id, post.id)

            # 刷新并验证计数不为负
            await db_session.refresh(post)
            assert post.like_count == 0


class TestLikeComment:
    """测试评论点赞功能"""

    @pytest.mark.asyncio
    async def test_like_comment_success(self, db_session: AsyncSession):
        """测试成功点赞评论"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "测试评论"
            )

        # Mock notification service for like
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            like, created = await like_service.like_comment(db_session, user.id, comment.id)

            # 验证点赞记录创建成功
            assert like is not None
            assert like.id is not None
            assert like.user_id == user.id
            assert like.target_type == "comment"
            assert like.target_id == comment.id
            assert created is True

    @pytest.mark.asyncio
    async def test_like_comment_increments_count(self, db_session: AsyncSession):
        """测试点赞增加评论计数"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "测试评论"
            )

        initial_count = comment.like_count or 0

        # Mock notification service for like
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            await like_service.like_comment(db_session, user.id, comment.id)

            # 刷新并验证计数增加
            await db_session.refresh(comment)
            assert comment.like_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_like_comment_idempotent(self, db_session: AsyncSession):
        """测试重复点赞评论幂等性"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "测试评论"
            )

        # Mock notification service for like
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 第一次点赞
            like1, created1 = await like_service.like_comment(db_session, user.id, comment.id)
            assert created1 is True

            # 第二次点赞（幂等）
            like2, created2 = await like_service.like_comment(db_session, user.id, comment.id)
            assert created2 is False
            assert like2.id == like1.id

            # 验证计数只增加一次
            await db_session.refresh(comment)
            assert comment.like_count == 1

    @pytest.mark.asyncio
    async def test_like_comment_sends_notification_to_author(self, db_session: AsyncSession):
        """测试点赞通知评论作者"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user1.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user1.id,
                "匿名用户",
                "测试评论"
            )

        # Mock notification service for like
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock) as mock_notify:
            await like_service.like_comment(db_session, user2.id, comment.id)

            # 验证发送了通知
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args[0]
            assert call_args[0] == db_session
            assert str(call_args[1]) == str(user1.id)
            assert call_args[2] == "like"
            assert call_args[3] == "新点赞"

    @pytest.mark.asyncio
    async def test_like_own_comment_no_notification(self, db_session: AsyncSession):
        """测试自己点赞自己的评论不发送通知"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "测试评论"
            )

        # Mock notification service for like
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock) as mock_notify:
            await like_service.like_comment(db_session, user.id, comment.id)

            # 验证没有发送通知
            mock_notify.assert_not_called()


class TestUnlikeComment:
    """测试评论取消点赞功能"""

    @pytest.mark.asyncio
    async def test_unlike_comment_success(self, db_session: AsyncSession):
        """测试成功取消点赞评论"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "测试评论"
            )

        # Mock notification service for like
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 先点赞
            await like_service.like_comment(db_session, user.id, comment.id)

            # 取消点赞
            result = await like_service.unlike_comment(db_session, user.id, comment.id)

            assert result is True

            # 验证点赞记录已被删除
            like = await like_service._get_like(db_session, user.id, "comment", comment.id)
            assert like is None

    @pytest.mark.asyncio
    async def test_unlike_comment_decrements_count(self, db_session: AsyncSession):
        """测试取消点赞减少评论计数"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "测试评论"
            )

        # Mock notification service for like
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 先点赞
            await like_service.like_comment(db_session, user.id, comment.id)
            await db_session.refresh(comment)
            initial_count = comment.like_count

            # 取消点赞
            await like_service.unlike_comment(db_session, user.id, comment.id)

            # 刷新并验证计数减少
            await db_session.refresh(comment)
            assert comment.like_count == max(0, initial_count - 1)

    @pytest.mark.asyncio
    async def test_unlike_comment_not_liked(self, db_session: AsyncSession):
        """测试取消未点赞的评论"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "测试评论"
            )

        # 取消未点赞的评论
        result = await like_service.unlike_comment(db_session, user.id, comment.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_unlike_comment_count_never_negative(self, db_session: AsyncSession):
        """测试评论点赞计数不会变成负数"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "测试评论"
            )

        # Mock notification service for like
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 先点赞
            await like_service.like_comment(db_session, user.id, comment.id)

            # 手动将计数设为0
            comment.like_count = 0
            await db_session.commit()

            # 取消点赞
            await like_service.unlike_comment(db_session, user.id, comment.id)

            # 刷新并验证计数不为负
            await db_session.refresh(comment)
            assert comment.like_count == 0


class TestIsLiked:
    """测试检查是否已点赞功能"""

    @pytest.mark.asyncio
    async def test_is_liked_post_true(self, db_session: AsyncSession):
        """测试检查帖子点赞状态 - 已点赞"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification and cache services
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock), \
             patch('app.services.like_service.LikeCacheService') as mock_cache:
            mock_cache.is_liked.return_value = False

            # 先点赞
            await like_service.like_post(db_session, user.id, post.id)

            # 检查点赞状态
            is_liked = await like_service.is_liked(db_session, user.id, "post", post.id)

            assert is_liked is True

    @pytest.mark.asyncio
    async def test_is_liked_post_false(self, db_session: AsyncSession):
        """测试检查帖子点赞状态 - 未点赞"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock cache service
        with patch('app.services.like_service.LikeCacheService') as mock_cache:
            mock_cache.is_liked.return_value = False

            # 检查点赞状态
            is_liked = await like_service.is_liked(db_session, user.id, "post", post.id)

            assert is_liked is False

    @pytest.mark.asyncio
    async def test_is_liked_comment_true(self, db_session: AsyncSession):
        """测试检查评论点赞状态 - 已点赞"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "测试评论"
            )

        # Mock notification and cache services
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock), \
             patch('app.services.like_service.LikeCacheService') as mock_cache:
            mock_cache.is_liked.return_value = False

            # 先点赞
            await like_service.like_comment(db_session, user.id, comment.id)

            # 检查点赞状态
            is_liked = await like_service.is_liked(db_session, user.id, "comment", comment.id)

            assert is_liked is True

    @pytest.mark.asyncio
    async def test_is_liked_comment_false(self, db_session: AsyncSession):
        """测试检查评论点赞状态 - 未点赞"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        from app.services import comment_service
        # Mock notification service for comment creation
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "测试评论"
            )

        # Mock cache service
        with patch('app.services.like_service.LikeCacheService') as mock_cache:
            mock_cache.is_liked.return_value = False

            # 检查点赞状态
            is_liked = await like_service.is_liked(db_session, user.id, "comment", comment.id)

            assert is_liked is False

    @pytest.mark.asyncio
    async def test_is_liked_checks_cache_first(self, db_session: AsyncSession):
        """测试优先检查缓存"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock cache service to return True (缓存命中)
        with patch('app.services.like_service.LikeCacheService') as mock_cache:
            mock_cache.is_liked.return_value = True

            # 检查点赞状态
            is_liked = await like_service.is_liked(db_session, user.id, "post", post.id)

            # 验证返回了缓存的结果
            assert is_liked is True
            # 验证调用了缓存检查
            mock_cache.is_liked.assert_called_once_with(user.id, "post", post.id)


class TestToggleLikeBehavior:
    """测试点赞/取消点赞的切换行为"""

    @pytest.mark.asyncio
    async def test_post_like_unlike_like_flow(self, db_session: AsyncSession):
        """测试帖子点赞->取消->再点赞的完整流程"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 点赞
            like1, created1 = await like_service.like_post(db_session, user.id, post.id)
            assert created1 is True
            await db_session.refresh(post)
            assert post.like_count == 1

            # 取消点赞
            result1 = await like_service.unlike_post(db_session, user.id, post.id)
            assert result1 is True
            await db_session.refresh(post)
            assert post.like_count == 0

            # 再次点赞
            like2, created2 = await like_service.like_post(db_session, user.id, post.id)
            assert created2 is True
            await db_session.refresh(post)
            assert post.like_count == 1

    @pytest.mark.asyncio
    async def test_multiple_users_like_same_post(self, db_session: AsyncSession):
        """测试多个用户点赞同一个帖子"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)
        user3 = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user1.id)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 三个用户都点赞
            await like_service.like_post(db_session, user1.id, post.id)
            await like_service.like_post(db_session, user2.id, post.id)
            await like_service.like_post(db_session, user3.id, post.id)

            # 验证计数
            await db_session.refresh(post)
            assert post.like_count == 3

            # 验证每个用户都有点赞记录
            assert await like_service.is_liked(db_session, user1.id, "post", post.id) is True
            assert await like_service.is_liked(db_session, user2.id, "post", post.id) is True
            assert await like_service.is_liked(db_session, user3.id, "post", post.id) is True

    @pytest.mark.asyncio
    async def test_user_likes_multiple_posts(self, db_session: AsyncSession):
        """测试一个用户点赞多个帖子"""
        user = await TestDataFactory.create_user(db_session)
        post1 = await TestDataFactory.create_post(db_session, user.id)
        post2 = await TestDataFactory.create_post(db_session, user.id)
        post3 = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification service
        with patch('app.services.like_service.notification_service.create_notification', new_callable=AsyncMock):
            # 点赞所有帖子
            await like_service.like_post(db_session, user.id, post1.id)
            await like_service.like_post(db_session, user.id, post2.id)
            await like_service.like_post(db_session, user.id, post3.id)

            # 验证每个帖子都有点赞记录和正确的计数
            await db_session.refresh(post1)
            await db_session.refresh(post2)
            await db_session.refresh(post3)

            assert post1.like_count == 1
            assert post2.like_count == 1
            assert post3.like_count == 1

            assert await like_service.is_liked(db_session, user.id, "post", post1.id) is True
            assert await like_service.is_liked(db_session, user.id, "post", post2.id) is True
            assert await like_service.is_liked(db_session, user.id, "post", post3.id) is True
