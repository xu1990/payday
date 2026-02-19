"""评论服务集成测试"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import comment_service
from app.core.exceptions import NotFoundException
from tests.test_utils import TestDataFactory


class TestListByPost:
    """测试按帖子获取评论列表"""

    @pytest.mark.asyncio
    async def test_list_by_post_empty(self, db_session: AsyncSession):
        """测试空列表"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        comments = await comment_service.list_by_post(db_session, post.id)

        assert comments == []

    @pytest.mark.asyncio
    async def test_list_by_post_success(self, db_session: AsyncSession):
        """测试成功获取评论列表"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建多个评论
        comment1 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户1",
            "第一条评论"
        )
        comment2 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户2",
            "第二条评论"
        )

        # 获取评论列表
        comments = await comment_service.list_by_post(db_session, post.id)

        assert len(comments) == 2
        assert comments[0].id == comment1.id
        assert comments[1].id == comment2.id
        assert comments[0].content == "第一条评论"
        assert comments[1].content == "第二条评论"

    @pytest.mark.asyncio
    async def test_list_by_post_ordered_by_created_at(self, db_session: AsyncSession):
        """测试评论按创建时间升序排列"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建评论
        comment1 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "第一条"
        )
        comment2 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "第二条"
        )

        # 获取评论列表
        comments = await comment_service.list_by_post(db_session, post.id)

        # 验证升序排列
        assert comments[0].id == comment1.id
        assert comments[1].id == comment2.id

    @pytest.mark.asyncio
    async def test_list_by_post_with_limit(self, db_session: AsyncSession):
        """测试限制返回数量"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建5个评论
        for i in range(5):
            await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                f"评论{i}"
            )

        # 只获取前3个
        comments = await comment_service.list_by_post(db_session, post.id, limit=3)

        assert len(comments) == 3

    @pytest.mark.asyncio
    async def test_list_by_post_with_offset(self, db_session: AsyncSession):
        """测试分页偏移"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建5个评论
        for i in range(5):
            await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                f"评论{i}"
            )

        # 跳过前2个，获取后面的
        comments = await comment_service.list_by_post(db_session, post.id, offset=2)

        assert len(comments) == 3


class TestListRootsWithReplies:
    """测试获取根评论及其回复的树形结构"""

    @pytest.mark.asyncio
    async def test_list_roots_with_replies_empty(self, db_session: AsyncSession):
        """测试空列表"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        roots = await comment_service.list_roots_with_replies(db_session, post.id)

        assert roots == []

    @pytest.mark.asyncio
    async def test_list_roots_without_replies(self, db_session: AsyncSession):
        """测试只有根评论没有回复"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建根评论
        root1 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "根评论1"
        )
        root2 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "根评论2"
        )

        # 获取根评论
        roots = await comment_service.list_roots_with_replies(db_session, post.id)

        assert len(roots) == 2
        assert roots[0].id == root1.id
        assert roots[1].id == root2.id
        # 验证 replies 属性存在且为空
        assert hasattr(roots[0], "replies")
        assert roots[0].replies == []
        assert hasattr(roots[1], "replies")
        assert roots[1].replies == []

    @pytest.mark.asyncio
    async def test_list_roots_with_replies_tree(self, db_session: AsyncSession):
        """测试根评论和回复的树形结构"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建根评论
        root1 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "根评论1"
        )
        root2 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "根评论2"
        )

        # 创建回复
        reply1 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "回复1-1",
            parent_id=root1.id
        )
        reply2 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "回复2-1",
            parent_id=root2.id
        )
        reply3 = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "回复1-2",
            parent_id=root1.id
        )

        # 获取根评论树
        roots = await comment_service.list_roots_with_replies(db_session, post.id)

        assert len(roots) == 2
        # 验证根评论1的回复
        assert roots[0].id == root1.id
        assert len(roots[0].replies) == 2
        reply_ids = [r.id for r in roots[0].replies]
        assert reply1.id in reply_ids
        assert reply3.id in reply_ids

        # 验证根评论2的回复
        assert roots[1].id == root2.id
        assert len(roots[1].replies) == 1
        assert roots[1].replies[0].id == reply2.id

    @pytest.mark.asyncio
    async def test_list_roots_with_replies_pagination(self, db_session: AsyncSession):
        """测试根评论分页"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建5个根评论
        roots = []
        for i in range(5):
            root = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                f"根评论{i}"
            )
            roots.append(root)

        # 分页获取
        page1 = await comment_service.list_roots_with_replies(
            db_session, post.id, limit=2, offset=0
        )
        page2 = await comment_service.list_roots_with_replies(
            db_session, post.id, limit=2, offset=2
        )
        page3 = await comment_service.list_roots_with_replies(
            db_session, post.id, limit=2, offset=4
        )

        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1


class TestCreateComment:
    """测试创建评论"""

    @pytest.mark.asyncio
    async def test_create_root_comment_success(self, db_session: AsyncSession):
        """测试成功创建根评论"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification service
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            comment = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "这是评论内容"
            )

            # 验证评论创建成功
            assert comment.id is not None
            assert comment.post_id == post.id
            assert comment.user_id == user.id
            assert comment.content == "这是评论内容"
            assert comment.anonymous_name == "匿名用户"
            assert comment.parent_id is None
            assert comment.like_count == 0
            assert comment.risk_status == "pending"

    @pytest.mark.asyncio
    async def test_create_reply_comment_success(self, db_session: AsyncSession):
        """测试成功创建回复"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建根评论
        parent = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "根评论"
        )

        # Mock notification service
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            reply = await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "这是回复",
                parent_id=parent.id
            )

            # 验证回复创建成功
            assert reply.id is not None
            assert reply.parent_id == parent.id
            assert reply.content == "这是回复"

    @pytest.mark.asyncio
    async def test_create_comment_increments_post_count(self, db_session: AsyncSession):
        """测试创建评论时增加帖子的评论计数"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        initial_count = post.comment_count or 0

        # Mock notification service
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock):
            await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "评论"
            )

            # 刷新并验证计数增加
            await db_session.refresh(post)
            assert post.comment_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_create_comment_sends_notification_to_post_author(self, db_session: AsyncSession):
        """测试根评论通知帖子作者"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user1.id)

        # Mock notification service
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock) as mock_notify:
            await comment_service.create(
                db_session,
                post.id,
                user2.id,  # 不同用户评论
                "匿名用户",
                "评论"
            )

            # 验证发送了通知 (db_session, user_id, type, title, content, related_id)
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args[0]
            assert call_args[0] == db_session  # 第一个参数是 db
            assert str(call_args[1]) == str(user1.id)  # 第二个参数是用户ID
            assert call_args[2] == "comment"
            assert call_args[3] == "新评论"

    @pytest.mark.asyncio
    async def test_create_reply_sends_notification_to_parent_author(self, db_session: AsyncSession):
        """测试回复通知被回复的人"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user1.id)

        # user1 创建根评论
        parent = await comment_service.create(
            db_session,
            post.id,
            user1.id,
            "匿名用户1",
            "根评论"
        )

        # Mock notification service
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock) as mock_notify:
            # user2 回复 user1
            await comment_service.create(
                db_session,
                post.id,
                user2.id,
                "匿名用户2",
                "回复",
                parent_id=parent.id
            )

            # 验证发送了通知 (db_session, user_id, type, title, content, related_id)
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args[0]
            assert call_args[0] == db_session  # 第一个参数是 db
            assert str(call_args[1]) == str(user1.id)  # 第二个参数是用户ID
            assert call_args[2] == "reply"
            assert call_args[3] == "新回复"

    @pytest.mark.asyncio
    async def test_create_own_comment_no_notification(self, db_session: AsyncSession):
        """测试自己评论自己的帖子不发送通知"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # Mock notification service
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock) as mock_notify:
            # 自己评论自己的帖子
            await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "自评论"
            )

            # 验证没有发送通知
            mock_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_own_reply_no_notification(self, db_session: AsyncSession):
        """测试自己回复自己的评论不发送通知"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建根评论
        parent = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "根评论"
        )

        # Mock notification service
        with patch('app.services.comment_service.notification_service.create_notification', new_callable=AsyncMock) as mock_notify:
            # 自己回复自己
            await comment_service.create(
                db_session,
                post.id,
                user.id,
                "匿名用户",
                "自回复",
                parent_id=parent.id
            )

            # 验证没有发送通知
            mock_notify.assert_not_called()


class TestGetById:
    """测试获取评论详情"""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, db_session: AsyncSession):
        """测试成功获取评论"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        comment = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "测试评论"
        )

        found = await comment_service.get_by_id(db_session, comment.id)

        assert found is not None
        assert found.id == comment.id
        assert found.content == "测试评论"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """测试获取不存在的评论"""
        found = await comment_service.get_by_id(db_session, "nonexistent_id")

        assert found is None


class TestDeleteComment:
    """测试删除评论"""

    @pytest.mark.asyncio
    async def test_delete_comment_success(self, db_session: AsyncSession):
        """测试成功删除评论"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        comment = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "测试评论"
        )

        # 删除评论
        result = await comment_service.delete(db_session, comment.id, user.id)

        assert result is True

        # 验证评论已被删除
        found = await comment_service.get_by_id(db_session, comment.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_comment_decrements_post_count(self, db_session: AsyncSession):
        """测试删除评论时减少帖子的评论计数"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        comment = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "测试评论"
        )

        # 刷新帖子获取最新的计数
        await db_session.refresh(post)
        initial_count = post.comment_count

        # 删除评论
        await comment_service.delete(db_session, comment.id, user.id)

        # 刷新并验证计数减少
        await db_session.refresh(post)
        assert post.comment_count == max(0, initial_count - 1)

    @pytest.mark.asyncio
    async def test_delete_comment_not_found(self, db_session: AsyncSession):
        """测试删除不存在的评论"""
        # 需要传递 user_id 参数
        result = await comment_service.delete(db_session, "nonexistent_id", "fake_user_id")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_comment_count_never_negative(self, db_session: AsyncSession):
        """测试评论计数不会变成负数"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建评论
        comment = await comment_service.create(
            db_session,
            post.id,
            user.id,
            "匿名用户",
            "测试评论"
        )

        # 手动将计数设为0
        post.comment_count = 0
        await db_session.commit()

        # 删除评论
        await comment_service.delete(db_session, comment.id, user.id)

        # 刷新并验证计数不为负
        await db_session.refresh(post)
        assert post.comment_count == 0


class TestListCommentsForAdmin:
    """测试管理员评论列表"""

    @pytest.mark.asyncio
    async def test_list_comments_for_admin_empty(self, db_session: AsyncSession):
        """测试空列表"""
        comments, total = await comment_service.list_comments_for_admin(db_session)

        assert total == 0
        assert comments == []

    @pytest.mark.asyncio
    async def test_list_comments_for_admin_success(self, db_session: AsyncSession):
        """测试管理员获取所有评论"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建多个评论
        await comment_service.create(db_session, post.id, user.id, "用户1", "评论1")
        await comment_service.create(db_session, post.id, user.id, "用户2", "评论2")
        await comment_service.create(db_session, post.id, user.id, "用户3", "评论3")

        # 获取列表
        comments, total = await comment_service.list_comments_for_admin(db_session)

        assert total == 3
        assert len(comments) == 3

    @pytest.mark.asyncio
    async def test_list_comments_for_admin_filter_by_post(self, db_session: AsyncSession):
        """测试按帖子筛选"""
        user = await TestDataFactory.create_user(db_session)
        post1 = await TestDataFactory.create_post(db_session, user.id)
        post2 = await TestDataFactory.create_post(db_session, user.id)

        # 为不同帖子创建评论
        await comment_service.create(db_session, post1.id, user.id, "用户", "帖子1评论1")
        await comment_service.create(db_session, post1.id, user.id, "用户", "帖子1评论2")
        await comment_service.create(db_session, post2.id, user.id, "用户", "帖子2评论")

        # 按帖子1筛选
        comments, total = await comment_service.list_comments_for_admin(
            db_session, post_id=post1.id
        )

        assert total == 2
        assert len(comments) == 2
        assert all(c.post_id == post1.id for c in comments)

    @pytest.mark.asyncio
    async def test_list_comments_for_admin_filter_by_risk_status(self, db_session: AsyncSession):
        """测试按风控状态筛选"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建不同风控状态的评论
        comment1 = await comment_service.create(db_session, post.id, user.id, "用户", "待审核")
        comment1.risk_status = "pending"
        await db_session.commit()

        comment2 = await comment_service.create(db_session, post.id, user.id, "用户", "已通过")
        comment2.risk_status = "approved"
        await db_session.commit()

        comment3 = await comment_service.create(db_session, post.id, user.id, "用户", "已拒绝")
        comment3.risk_status = "rejected"
        await db_session.commit()

        # 筛选待审核的评论
        comments, total = await comment_service.list_comments_for_admin(
            db_session, risk_status="pending"
        )

        assert total == 1
        assert len(comments) == 1
        assert comments[0].risk_status == "pending"

    @pytest.mark.asyncio
    async def test_list_comments_for_admin_pagination(self, db_session: AsyncSession):
        """测试分页功能"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建5个评论
        for i in range(5):
            await comment_service.create(db_session, post.id, user.id, "用户", f"评论{i}")

        # 分页获取
        page1, total1 = await comment_service.list_comments_for_admin(
            db_session, limit=2, offset=0
        )
        page2, total2 = await comment_service.list_comments_for_admin(
            db_session, limit=2, offset=2
        )
        page3, total3 = await comment_service.list_comments_for_admin(
            db_session, limit=2, offset=4
        )

        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1
        assert total1 == total2 == total3 == 5

    @pytest.mark.asyncio
    async def test_list_comments_for_admin_ordered_by_created_at_desc(self, db_session: AsyncSession):
        """测试按创建时间倒序排列（最新的在前）"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        # 创建评论
        comment1 = await comment_service.create(db_session, post.id, user.id, "用户", "评论1")
        comment2 = await comment_service.create(db_session, post.id, user.id, "用户", "评论2")
        comment3 = await comment_service.create(db_session, post.id, user.id, "用户", "评论3")

        # 获取列表
        comments, total = await comment_service.list_comments_for_admin(db_session)

        assert total == 3
        # 验证倒序排列（最新的在前）
        assert comments[0].id == comment3.id
        assert comments[1].id == comment2.id
        assert comments[2].id == comment1.id


class TestUpdateCommentRiskForAdmin:
    """测试管理员更新评论风控状态"""

    @pytest.mark.asyncio
    async def test_update_comment_risk_status_to_approved(self, db_session: AsyncSession):
        """测试审核通过评论"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        comment = await comment_service.create(db_session, post.id, user.id, "用户", "测试评论")

        # 审核通过
        updated = await comment_service.update_comment_risk_for_admin(
            db_session,
            comment.id,
            risk_status="approved"
        )

        assert updated is not None
        assert updated.risk_status == "approved"

    @pytest.mark.asyncio
    async def test_update_comment_risk_status_to_rejected(self, db_session: AsyncSession):
        """测试拒绝评论"""
        user = await TestDataFactory.create_user(db_session)
        post = await TestDataFactory.create_post(db_session, user.id)

        comment = await comment_service.create(db_session, post.id, user.id, "用户", "测试评论")

        # 拒绝并填写原因
        updated = await comment_service.update_comment_risk_for_admin(
            db_session,
            comment.id,
            risk_status="rejected",
            risk_reason="包含违规内容"
        )

        assert updated is not None
        assert updated.risk_status == "rejected"

    @pytest.mark.asyncio
    async def test_update_comment_risk_status_not_found(self, db_session: AsyncSession):
        """测试更新不存在的评论"""
        with pytest.raises(NotFoundException) as exc_info:
            await comment_service.update_comment_risk_for_admin(
                db_session,
                "nonexistent_id",
                risk_status="approved"
            )

        assert "评论不存在" in str(exc_info.value)
