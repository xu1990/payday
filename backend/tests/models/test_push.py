"""
单元测试 - 推送通知模型 (app.models.push)
"""
import pytest
from datetime import datetime
from sqlalchemy import select

from app.models.push import PushNotification


class TestPushNotification:
    """测试推送通知模型"""

    def test_table_name(self):
        """测试表名"""
        assert PushNotification.__tablename__ == "push_notifications"

    def test_columns(self):
        """测试列定义"""
        # 验证列存在
        assert hasattr(PushNotification, 'id')
        assert hasattr(PushNotification, 'user_id')
        assert hasattr(PushNotification, 'title')
        assert hasattr(PushNotification, 'content')
        assert hasattr(PushNotification, 'type')
        assert hasattr(PushNotification, 'target_type')
        assert hasattr(PushNotification, 'target_id')
        assert hasattr(PushNotification, 'is_sent')
        assert hasattr(PushNotification, 'sent_at')
        assert hasattr(PushNotification, 'created_at')

    @pytest.mark.asyncio
    async def test_create_instance(self, db_session):
        """测试创建实例"""
        notification = PushNotification(
            user_id="test_user_id",
            title="测试标题",
            content="测试内容",
            type="system",
            target_type="post",
            target_id="test_post_id",
            is_sent=False,
        )

        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)

        assert notification.id is not None
        assert notification.user_id == "test_user_id"
        assert notification.title == "测试标题"
        assert notification.content == "测试内容"
        assert notification.type == "system"
        assert notification.target_type == "post"
        assert notification.target_id == "test_post_id"
        assert notification.is_sent is False
        assert notification.created_at is not None

    @pytest.mark.asyncio
    async def test_default_values(self, db_session):
        """测试默认值"""
        notification = PushNotification(
            user_id="test_user_id",
            title="测试标题",
            type="promotion",
        )

        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)

        assert notification.is_sent is False
        assert notification.created_at is not None
        assert notification.content is None
        assert notification.target_type is None
        assert notification.target_id is None
        assert notification.sent_at is None

    @pytest.mark.asyncio
    async def test_sent_status(self, db_session):
        """测试发送状态"""
        notification = PushNotification(
            user_id="test_user_id",
            title="测试标题",
            type="payday",
        )

        db_session.add(notification)
        await db_session.commit()

        # 标记为已发送
        notification.is_sent = True
        notification.sent_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(notification)

        assert notification.is_sent is True
        assert notification.sent_at is not None

    @pytest.mark.asyncio
    async def test_push_types(self, db_session):
        """测试不同推送类型"""
        types = ["system", "promotion", "payday"]

        for push_type in types:
            notification = PushNotification(
                user_id="test_user_id",
                title=f"{push_type}标题",
                type=push_type,
            )
            db_session.add(notification)

        await db_session.commit()

        # 验证所有类型都创建成功
        notifications = await db_session.execute(
            select(PushNotification).where(PushNotification.user_id == "test_user_id")
        )
        results = list(notifications.scalars().all())
        assert len(results) == len(types)
        assert {n.type for n in results} == set(types)

    @pytest.mark.asyncio
    async def test_target_types(self, db_session):
        """测试不同跳转类型"""
        target_types = ["post", "user", "web", None]

        for idx, target_type in enumerate(target_types):
            notification = PushNotification(
                user_id="test_user_id",
                title=f"测试{idx}",
                type="system",
                target_type=target_type,
                target_id=f"target_{idx}" if target_type else None,
            )
            db_session.add(notification)

        await db_session.commit()

        # 验证所有类型都创建成功
        notifications = await db_session.execute(
            select(PushNotification).where(PushNotification.user_id == "test_user_id")
        )
        results = list(notifications.scalars().all())
        assert len(results) == len(target_types)

    @pytest.mark.asyncio
    async def test_optional_content(self, db_session):
        """测试可选内容"""
        notification = PushNotification(
            user_id="test_user_id",
            title="只有标题",
            type="system",
            # content 不设置
        )

        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)

        assert notification.title == "只有标题"
        assert notification.content is None
