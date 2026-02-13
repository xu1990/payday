"""通知服务测试"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import notification_service
from app.models.notification import Notification
from tests.test_utils import TestDataFactory


class TestCreateNotification:
    """测试创建通知功能"""

    @pytest.mark.asyncio
    async def test_create_notification_basic(self, db_session: AsyncSession):
        """测试创建基本通知"""
        user = await TestDataFactory.create_user(db_session, "user1")

        notification = await notification_service.create_notification(
            db_session,
            user_id=user.id,
            type="system",
            title="系统通知",
            content="这是一条测试通知",
        )

        # 验证通知创建成功
        assert notification.id is not None
        assert notification.user_id == user.id
        assert notification.type == "system"
        assert notification.title == "系统通知"
        assert notification.content == "这是一条测试通知"
        assert notification.is_read is False

    @pytest.mark.asyncio
    async def test_create_notification_with_related_id(self, db_session: AsyncSession):
        """测试创建带关联ID的通知"""
        user = await TestDataFactory.create_user(db_session, "user1")
        post = await TestDataFactory.create_post(db_session, user.id, "测试帖子")

        notification = await notification_service.create_notification(
            db_session,
            user_id=user.id,
            type="comment",
            title="新评论",
            content="有人评论了你的帖子",
            related_id=post.id,
        )

        # 验证关联ID正确保存
        assert notification.related_id == post.id

    @pytest.mark.asyncio
    async def test_create_notification_all_types(self, db_session: AsyncSession):
        """测试创建所有类型的通知"""
        user = await TestDataFactory.create_user(db_session, "user1")

        notification_types = ["comment", "reply", "like", "system"]

        for notif_type in notification_types:
            notification = await notification_service.create_notification(
                db_session,
                user_id=user.id,
                type=notif_type,
                title=f"{notif_type}通知",
                content=f"这是一条{notif_type}类型的通知",
            )

            assert notification.type == notif_type

    @pytest.mark.asyncio
    async def test_create_notification_without_content(self, db_session: AsyncSession):
        """测试创建无内容的通知"""
        user = await TestDataFactory.create_user(db_session, "user1")

        notification = await notification_service.create_notification(
            db_session,
            user_id=user.id,
            type="system",
            title="简单通知",
        )

        # 验证通知创建成功，content为None
        assert notification.id is not None
        assert notification.content is None


class TestListNotifications:
    """测试通知列表功能"""

    @pytest.mark.asyncio
    async def test_list_notifications_empty(self, db_session: AsyncSession):
        """测试空通知列表"""
        user = await TestDataFactory.create_user(db_session, "user1")

        notifications, total = await notification_service.list_notifications(
            db_session, user.id
        )

        assert notifications == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_notifications_single(self, db_session: AsyncSession):
        """测试单条通知列表"""
        user = await TestDataFactory.create_user(db_session, "user1")
        await TestDataFactory.create_notification(
            db_session, user.id, "system", "系统通知", "内容"
        )

        notifications, total = await notification_service.list_notifications(
            db_session, user.id
        )

        assert len(notifications) == 1
        assert total == 1
        assert notifications[0].title == "系统通知"

    @pytest.mark.asyncio
    async def test_list_notifications_multiple(self, db_session: AsyncSession):
        """测试多条通知列表"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建多条通知
        await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        await TestDataFactory.create_notification(
            db_session, user.id, "comment", "通知2", "内容2"
        )
        await TestDataFactory.create_notification(
            db_session, user.id, "like", "通知3", "内容3"
        )

        notifications, total = await notification_service.list_notifications(
            db_session, user.id
        )

        assert len(notifications) == 3
        assert total == 3

    @pytest.mark.asyncio
    async def test_list_notifications_ordered_by_created_at_desc(
        self, db_session: AsyncSession
    ):
        """测试通知列表按创建时间倒序排列"""
        import time

        user = await TestDataFactory.create_user(db_session, "user1")

        # 按顺序创建通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        time.sleep(0.01)  # 小延迟确保时间戳不同

        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        time.sleep(0.01)

        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        notifications, total = await notification_service.list_notifications(
            db_session, user.id
        )

        # 验证倒序排列（最新的在前）
        assert len(notifications) == 3
        assert total == 3
        assert notifications[0].id == notif3.id
        assert notifications[1].id == notif2.id
        assert notifications[2].id == notif1.id

    @pytest.mark.asyncio
    async def test_list_notifications_unread_only(self, db_session: AsyncSession):
        """测试只获取未读通知"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建3条通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        # 标记notif2为已读
        await notification_service.mark_one_read(db_session, user.id, notif2.id)

        # 获取未读通知
        notifications, total = await notification_service.list_notifications(
            db_session, user.id, unread_only=True
        )

        # 应该只返回2条未读通知
        assert len(notifications) == 2
        assert total == 2
        notification_ids = [n.id for n in notifications]
        assert notif1.id in notification_ids
        assert notif3.id in notification_ids
        assert notif2.id not in notification_ids

    @pytest.mark.asyncio
    async def test_list_notifications_with_type_filter(self, db_session: AsyncSession):
        """测试按类型过滤通知"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建不同类型的通知
        await TestDataFactory.create_notification(
            db_session, user.id, "system", "系统通知", "内容1"
        )
        await TestDataFactory.create_notification(
            db_session, user.id, "comment", "评论通知", "内容2"
        )
        await TestDataFactory.create_notification(
            db_session, user.id, "like", "点赞通知", "内容3"
        )

        # 只获取comment类型的通知
        notifications, total = await notification_service.list_notifications(
            db_session, user.id, type_filter="comment"
        )

        assert len(notifications) == 1
        assert total == 1
        assert notifications[0].type == "comment"

    @pytest.mark.asyncio
    async def test_list_notifications_with_pagination(self, db_session: AsyncSession):
        """测试通知列表分页"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建5条通知
        for i in range(5):
            await TestDataFactory.create_notification(
                db_session, user.id, "system", f"通知{i+1}", f"内容{i+1}"
            )

        # 第一页：3条
        notifications1, total1 = await notification_service.list_notifications(
            db_session, user.id, limit=3, offset=0
        )
        assert len(notifications1) == 3
        assert total1 == 5

        # 第二页：2条
        notifications2, total2 = await notification_service.list_notifications(
            db_session, user.id, limit=3, offset=3
        )
        assert len(notifications2) == 2
        assert total2 == 5

        # 验证没有重复
        ids1 = [n.id for n in notifications1]
        ids2 = [n.id for n in notifications2]
        assert set(ids1).isdisjoint(set(ids2))

    @pytest.mark.asyncio
    async def test_list_notifications_only_user_own(self, db_session: AsyncSession):
        """测试只能看到自己的通知"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 为user1创建通知
        await TestDataFactory.create_notification(
            db_session, user1.id, "system", "用户1的通知", "内容1"
        )

        # 为user2创建通知
        await TestDataFactory.create_notification(
            db_session, user2.id, "system", "用户2的通知", "内容2"
        )

        # user1获取通知列表
        notifications1, total1 = await notification_service.list_notifications(
            db_session, user1.id
        )

        # user2获取通知列表
        notifications2, total2 = await notification_service.list_notifications(
            db_session, user2.id
        )

        # 验证各自只能看到自己的通知
        assert len(notifications1) == 1
        assert total1 == 1
        assert notifications1[0].user_id == user1.id

        assert len(notifications2) == 1
        assert total2 == 1
        assert notifications2[0].user_id == user2.id


class TestGetUnreadCount:
    """测试获取未读通知数量功能"""

    @pytest.mark.asyncio
    async def test_get_unread_count_zero(self, db_session: AsyncSession):
        """测试没有通知时未读数为0"""
        user = await TestDataFactory.create_user(db_session, "user1")

        count = await notification_service.get_unread_count(db_session, user.id)

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_unread_count_all_unread(self, db_session: AsyncSession):
        """测试全部未读通知计数"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建3条未读通知
        await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        count = await notification_service.get_unread_count(db_session, user.id)

        assert count == 3

    @pytest.mark.asyncio
    async def test_get_unread_count_partial_read(self, db_session: AsyncSession):
        """测试部分已读通知计数"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建3条通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        # 标记其中一条为已读
        await notification_service.mark_one_read(db_session, user.id, notif2.id)

        count = await notification_service.get_unread_count(db_session, user.id)

        assert count == 2

    @pytest.mark.asyncio
    async def test_get_unread_count_all_read(self, db_session: AsyncSession):
        """测试全部已读时计数为0"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建3条通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        # 标记全部为已读
        await notification_service.mark_all_read(db_session, user.id)

        count = await notification_service.get_unread_count(db_session, user.id)

        assert count == 0


class TestMarkRead:
    """测试批量标记已读功能"""

    @pytest.mark.asyncio
    async def test_mark_read_single(self, db_session: AsyncSession):
        """测试标记单条通知已读"""
        user = await TestDataFactory.create_user(db_session, "user1")
        notification = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知", "内容"
        )

        # 标记已读
        count = await notification_service.mark_read(
            db_session, user.id, [notification.id]
        )

        # 验证返回更新条数
        assert count == 1

        # 验证通知已标记为已读
        await db_session.refresh(notification)
        assert notification.is_read is True

    @pytest.mark.asyncio
    async def test_mark_read_multiple(self, db_session: AsyncSession):
        """测试批量标记多条通知已读"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建3条通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        # 批量标记已读
        count = await notification_service.mark_read(
            db_session, user.id, [notif1.id, notif2.id, notif3.id]
        )

        # 验证返回更新条数
        assert count == 3

        # 验证所有通知都已标记为已读
        await db_session.refresh(notif1)
        await db_session.refresh(notif2)
        await db_session.refresh(notif3)
        assert notif1.is_read is True
        assert notif2.is_read is True
        assert notif3.is_read is True

    @pytest.mark.asyncio
    async def test_mark_read_partial(self, db_session: AsyncSession):
        """测试批量标记部分通知已读"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建3条通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        # 只标记前两条
        count = await notification_service.mark_read(
            db_session, user.id, [notif1.id, notif2.id]
        )

        # 验证返回更新条数
        assert count == 2

        # 验证只有前两条被标记
        await db_session.refresh(notif1)
        await db_session.refresh(notif2)
        await db_session.refresh(notif3)
        assert notif1.is_read is True
        assert notif2.is_read is True
        assert notif3.is_read is False

    @pytest.mark.asyncio
    async def test_mark_read_empty_list(self, db_session: AsyncSession):
        """测试标记空列表返回0"""
        user = await TestDataFactory.create_user(db_session, "user1")

        count = await notification_service.mark_read(db_session, user.id, [])

        assert count == 0

    @pytest.mark.asyncio
    async def test_mark_read_nonexistent_notification(self, db_session: AsyncSession):
        """测试标记不存在的通知返回0"""
        user = await TestDataFactory.create_user(db_session, "user1")

        count = await notification_service.mark_read(
            db_session, user.id, ["nonexistent_id"]
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_mark_read_only_own_notifications(self, db_session: AsyncSession):
        """测试只能标记自己的通知"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 为user2创建通知
        notif = await TestDataFactory.create_notification(
            db_session, user2.id, "system", "用户2的通知", "内容"
        )

        # user1尝试标记user2的通知（应该失败）
        count = await notification_service.mark_read(
            db_session, user1.id, [notif.id]
        )

        # 验证没有更新任何记录
        assert count == 0

        # 验证通知仍然是未读
        await db_session.refresh(notif)
        assert notif.is_read is False


class TestMarkAllRead:
    """测试全部标记已读功能"""

    @pytest.mark.asyncio
    async def test_mark_all_read_empty(self, db_session: AsyncSession):
        """测试没有通知时标记全部已读返回0"""
        user = await TestDataFactory.create_user(db_session, "user1")

        count = await notification_service.mark_all_read(db_session, user.id)

        assert count == 0

    @pytest.mark.asyncio
    async def test_mark_all_read_multiple(self, db_session: AsyncSession):
        """测试标记全部通知已读"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建3条通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        # 标记全部已读
        count = await notification_service.mark_all_read(db_session, user.id)

        # 验证返回更新条数
        assert count == 3

        # 验证所有通知都已标记为已读
        await db_session.refresh(notif1)
        await db_session.refresh(notif2)
        await db_session.refresh(notif3)
        assert notif1.is_read is True
        assert notif2.is_read is True
        assert notif3.is_read is True

    @pytest.mark.asyncio
    async def test_mark_all_read_partial_already_read(self, db_session: AsyncSession):
        """测试部分已读时标记全部已读"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建3条通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        # 先标记一条为已读
        await notification_service.mark_one_read(db_session, user.id, notif1.id)

        # 标记全部已读
        count = await notification_service.mark_all_read(db_session, user.id)

        # 验证只更新了未读的2条
        assert count == 2

        # 验证所有通知都已标记为已读
        await db_session.refresh(notif1)
        await db_session.refresh(notif2)
        await db_session.refresh(notif3)
        assert notif1.is_read is True
        assert notif2.is_read is True
        assert notif3.is_read is True

    @pytest.mark.asyncio
    async def test_mark_all_read_only_own_notifications(self, db_session: AsyncSession):
        """测试标记全部已读只影响自己的通知"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 为两个用户各创建通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user1.id, "system", "用户1的通知", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user2.id, "system", "用户2的通知", "内容2"
        )

        # user1标记全部已读
        count = await notification_service.mark_all_read(db_session, user1.id)

        # 验证只更新了1条
        assert count == 1

        # 验证user1的通知已读
        await db_session.refresh(notif1)
        assert notif1.is_read is True

        # 验证user2的通知仍然是未读
        await db_session.refresh(notif2)
        assert notif2.is_read is False


class TestMarkOneRead:
    """测试标记单条通知已读功能"""

    @pytest.mark.asyncio
    async def test_mark_one_read_success(self, db_session: AsyncSession):
        """测试成功标记单条通知已读"""
        user = await TestDataFactory.create_user(db_session, "user1")
        notification = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知", "内容"
        )

        # 标记已读
        result = await notification_service.mark_one_read(
            db_session, user.id, notification.id
        )

        # 验证返回True
        assert result is True

        # 验证通知已标记为已读
        await db_session.refresh(notification)
        assert notification.is_read is True

    @pytest.mark.asyncio
    async def test_mark_one_read_already_read(self, db_session: AsyncSession):
        """测试标记已读的通知仍返回True"""
        user = await TestDataFactory.create_user(db_session, "user1")
        notification = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知", "内容"
        )

        # 第一次标记
        result1 = await notification_service.mark_one_read(
            db_session, user.id, notification.id
        )
        assert result1 is True

        # 第二次标记（已经已读）
        result2 = await notification_service.mark_one_read(
            db_session, user.id, notification.id
        )
        # SQLAlchemy的update会返回匹配的行数，即使值没有变化
        # 所以这里应该返回True
        assert result2 is True

    @pytest.mark.asyncio
    async def test_mark_one_read_nonexistent_notification(self, db_session: AsyncSession):
        """测试标记不存在的通知返回False"""
        user = await TestDataFactory.create_user(db_session, "user1")

        result = await notification_service.mark_one_read(
            db_session, user.id, "nonexistent_id"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_mark_one_read_only_own_notification(self, db_session: AsyncSession):
        """测试只能标记自己的通知"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 为user2创建通知
        notification = await TestDataFactory.create_notification(
            db_session, user2.id, "system", "用户2的通知", "内容"
        )

        # user1尝试标记user2的通知（应该失败）
        result = await notification_service.mark_one_read(
            db_session, user1.id, notification.id
        )

        # 验证返回False
        assert result is False

        # 验证通知仍然是未读
        await db_session.refresh(notification)
        assert notification.is_read is False


class TestDeleteNotifications:
    """测试删除通知功能"""

    @pytest.mark.asyncio
    async def test_delete_notifications_single(self, db_session: AsyncSession):
        """测试删除单条通知"""
        user = await TestDataFactory.create_user(db_session, "user1")
        notification = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知", "内容"
        )

        # 删除通知
        count = await notification_service.delete_notifications(
            db_session, user.id, notification_ids=[notification.id]
        )

        # 验证返回删除条数
        assert count == 1

        # 验证通知已被删除
        from sqlalchemy import select

        result = await db_session.execute(
            select(Notification).where(Notification.id == notification.id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_notifications_multiple(self, db_session: AsyncSession):
        """测试批量删除多条通知"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建3条通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        # 删除前两条
        count = await notification_service.delete_notifications(
            db_session, user.id, notification_ids=[notif1.id, notif2.id]
        )

        # 验证返回删除条数
        assert count == 2

        # 验证通知已被删除
        from sqlalchemy import select

        result = await db_session.execute(
            select(Notification).where(Notification.id.in_([notif1.id, notif2.id]))
        )
        assert result.scalars().all() == []

        # 验证第三条仍然存在
        result3 = await db_session.execute(
            select(Notification).where(Notification.id == notif3.id)
        )
        assert result3.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_delete_notifications_all(self, db_session: AsyncSession):
        """测试删除全部通知"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建3条通知
        await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        # 删除全部
        count = await notification_service.delete_notifications(
            db_session, user.id, delete_all=True
        )

        # 验证返回删除条数
        assert count == 3

        # 验证所有通知都被删除
        notifications, total = await notification_service.list_notifications(
            db_session, user.id
        )
        assert len(notifications) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_delete_notifications_empty_params(self, db_session: AsyncSession):
        """测试不传参数时返回0"""
        user = await TestDataFactory.create_user(db_session, "user1")

        count = await notification_service.delete_notifications(
            db_session, user.id, notification_ids=None, delete_all=False
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_delete_notifications_nonexistent(self, db_session: AsyncSession):
        """测试删除不存在的通知返回0"""
        user = await TestDataFactory.create_user(db_session, "user1")

        count = await notification_service.delete_notifications(
            db_session, user.id, notification_ids=["nonexistent_id"]
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_delete_notifications_only_own(self, db_session: AsyncSession):
        """测试只能删除自己的通知"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 为user2创建通知
        notification = await TestDataFactory.create_notification(
            db_session, user2.id, "system", "用户2的通知", "内容"
        )

        # user1尝试删除user2的通知（应该失败）
        count = await notification_service.delete_notifications(
            db_session, user1.id, notification_ids=[notification.id]
        )

        # 验证没有删除任何记录
        assert count == 0

        # 验证通知仍然存在
        await db_session.refresh(notification)
        assert notification is not None


class TestNotificationWorkflow:
    """测试通知完整流程"""

    @pytest.mark.asyncio
    async def test_create_read_unread_workflow(self, db_session: AsyncSession):
        """测试创建->读取->未读数的完整流程"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 1. 创建3条通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知1", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知2", "内容2"
        )
        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "通知3", "内容3"
        )

        # 2. 获取未读数
        unread_count = await notification_service.get_unread_count(db_session, user.id)
        assert unread_count == 3

        # 3. 获取通知列表
        notifications, total = await notification_service.list_notifications(
            db_session, user.id
        )
        assert len(notifications) == 3
        assert total == 3

        # 4. 标记其中两条已读
        await notification_service.mark_read(
            db_session, user.id, [notif1.id, notif2.id]
        )

        # 5. 再次获取未读数
        unread_count = await notification_service.get_unread_count(db_session, user.id)
        assert unread_count == 1

        # 6. 标记全部已读
        await notification_service.mark_all_read(db_session, user.id)

        # 7. 验证未读数为0
        unread_count = await notification_service.get_unread_count(db_session, user.id)
        assert unread_count == 0

    @pytest.mark.asyncio
    async def test_create_delete_workflow(self, db_session: AsyncSession):
        """测试创建->删除的完整流程"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 1. 创建5条通知
        notifications_to_create = []
        for i in range(5):
            notif = await TestDataFactory.create_notification(
                db_session, user.id, "system", f"通知{i+1}", f"内容{i+1}"
            )
            notifications_to_create.append(notif)

        # 2. 验证创建成功
        notifications, total = await notification_service.list_notifications(
            db_session, user.id
        )
        assert len(notifications) == 5
        assert total == 5

        # 3. 删除3条
        await notification_service.delete_notifications(
            db_session,
            user.id,
            notification_ids=[
                notifications_to_create[0].id,
                notifications_to_create[1].id,
                notifications_to_create[2].id,
            ],
        )

        # 4. 验证剩余2条
        notifications, total = await notification_service.list_notifications(
            db_session, user.id
        )
        assert len(notifications) == 2
        assert total == 2

        # 5. 删除全部
        await notification_service.delete_notifications(
            db_session, user.id, delete_all=True
        )

        # 6. 验证全部删除
        notifications, total = await notification_service.list_notifications(
            db_session, user.id
        )
        assert len(notifications) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_filter_and_pagination_workflow(self, db_session: AsyncSession):
        """测试过滤和分页的完整流程"""
        user = await TestDataFactory.create_user(db_session, "user1")

        # 创建不同类型的通知
        notif1 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "系统通知1", "内容1"
        )
        notif2 = await TestDataFactory.create_notification(
            db_session, user.id, "comment", "评论通知1", "内容2"
        )
        notif3 = await TestDataFactory.create_notification(
            db_session, user.id, "like", "点赞通知1", "内容3"
        )
        notif4 = await TestDataFactory.create_notification(
            db_session, user.id, "comment", "评论通知2", "内容4"
        )
        notif5 = await TestDataFactory.create_notification(
            db_session, user.id, "system", "系统通知2", "内容5"
        )

        # 1. 获取全部通知
        all_notifications, total = await notification_service.list_notifications(
            db_session, user.id
        )
        assert total == 5

        # 2. 按类型过滤（comment）
        comment_notifications, comment_total = (
            await notification_service.list_notifications(
                db_session, user.id, type_filter="comment"
            )
        )
        assert comment_total == 2
        assert all(n.type == "comment" for n in comment_notifications)

        # 3. 获取未读通知
        unread_notifications, unread_total = (
            await notification_service.list_notifications(
                db_session, user.id, unread_only=True
            )
        )
        assert unread_total == 5

        # 4. 标记一些已读后获取未读
        await notification_service.mark_read(
            db_session, user.id, [notif1.id, notif2.id]
        )
        unread_notifications, unread_total = (
            await notification_service.list_notifications(
                db_session, user.id, unread_only=True
            )
        )
        assert unread_total == 3

        # 5. 分页获取
        page1, total1 = await notification_service.list_notifications(
            db_session, user.id, limit=2, offset=0
        )
        assert len(page1) == 2
        assert total1 == 5

        page2, total2 = await notification_service.list_notifications(
            db_session, user.id, limit=2, offset=2
        )
        assert len(page2) == 2
        assert total2 == 5

        page3, total3 = await notification_service.list_notifications(
            db_session, user.id, limit=2, offset=4
        )
        assert len(page3) == 1
        assert total3 == 5
