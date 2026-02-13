"""测试工具和数据工厂"""
import uuid
from datetime import datetime, timedelta, date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.salary import SalaryRecord
from app.models.membership import Membership, MembershipOrder
from app.models.notification import Notification
from app.utils.encryption import encrypt_amount


class TestDataFactory:
    """测试数据工厂"""

    @staticmethod
    async def create_user(
        db_session: AsyncSession,
        openid: str = None,
        anonymous_name: str = "测试用户",
        **kwargs
    ) -> User:
        """创建测试用户"""
        if openid is None:
            openid = f"test_{uuid.uuid4().hex[:16]}"

        user = User(
            openid=openid,
            anonymous_name=anonymous_name,
            avatar=kwargs.get("avatar"),
            bio=kwargs.get("bio"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @staticmethod
    async def create_post(
        db_session: AsyncSession,
        user_id: str,
        content: str = "测试内容",
        **kwargs
    ) -> Post:
        """创建测试帖子"""
        post = Post(
            user_id=user_id,
            anonymous_name=kwargs.get("anonymous_name", "匿名用户"),
            content=content,
            images=kwargs.get("images", []),
            tags=kwargs.get("tags", []),
            type=kwargs.get("type", "complaint"),
            salary_range=kwargs.get("salary_range"),
            industry=kwargs.get("industry"),
            city=kwargs.get("city"),
            risk_status=kwargs.get("risk_status", "pending"),
            status=kwargs.get("status", "normal"),
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)
        return post

    @staticmethod
    async def create_comment(
        db_session: AsyncSession,
        user_id: str,
        post_id: str,
        content: str = "测试评论",
        **kwargs
    ) -> Comment:
        """创建测试评论"""
        comment = Comment(
            user_id=user_id,
            post_id=post_id,
            anonymous_name=kwargs.get("anonymous_name", "匿名用户"),
            content=content,
        )
        db_session.add(comment)
        await db_session.commit()
        await db_session.refresh(comment)
        return comment

    @staticmethod
    async def create_salary(
        db_session: AsyncSession,
        user_id: str,
        config_id: str,
        amount: int = 10000,
        payday_date: Optional[date] = None,
        **kwargs
    ) -> SalaryRecord:
        """创建测试薪资记录"""
        if payday_date is None:
            payday_date = datetime.now().date()

        amount_encrypted, encryption_salt = encrypt_amount(amount)

        salary = SalaryRecord(
            user_id=user_id,
            config_id=config_id,
            amount_encrypted=amount_encrypted,
            encryption_salt=encryption_salt,
            payday_date=payday_date,
            salary_type=kwargs.get("salary_type", "normal"),
            pre_tax_amount=kwargs.get("pre_tax_amount"),
            tax_amount=kwargs.get("tax_amount"),
            source=kwargs.get("source"),
            delayed_days=kwargs.get("delayed_days"),
            images=kwargs.get("images", []),
            note=kwargs.get("note"),
            mood=kwargs.get("mood", "happy"),
        )
        db_session.add(salary)
        await db_session.commit()
        await db_session.refresh(salary)
        return salary

    @staticmethod
    async def create_membership(
        db_session: AsyncSession,
        name: str = "月度会员",
        price: int = 9900,
        duration_days: int = 30,
        **kwargs
    ) -> Membership:
        """创建测试会员套餐"""
        membership = Membership(
            name=name,
            description=kwargs.get("description"),
            price=price,
            duration_days=duration_days,
            is_active=kwargs.get("is_active", 1),
            sort_order=kwargs.get("sort_order", 0),
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)
        return membership

    @staticmethod
    async def create_order(
        db_session: AsyncSession,
        user_id: str,
        membership_id: str = None,
        amount: int = 9900,
        status: str = "pending",
        **kwargs
    ) -> MembershipOrder:
        """创建测试订单"""
        now = datetime.utcnow()
        start_date = kwargs.get("start_date", now)
        duration_days = kwargs.get("duration_days", 30)
        end_date = kwargs.get("end_date", now + timedelta(days=duration_days))

        order = MembershipOrder(
            user_id=user_id,
            membership_id=membership_id,
            amount=amount,
            status=status,
            payment_method=kwargs.get("payment_method"),
            transaction_id=kwargs.get("transaction_id"),
            start_date=start_date,
            end_date=end_date,
            auto_renew=kwargs.get("auto_renew", 0),
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        return order

    @staticmethod
    async def create_notification(
        db_session: AsyncSession,
        user_id: str,
        type: str = "system",
        title: str = "测试通知",
        content: str = "这是测试内容",
        **kwargs
    ) -> Notification:
        """创建测试通知"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            related_id=kwargs.get("related_id"),
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        return notification
