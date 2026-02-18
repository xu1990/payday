"""
测试辅助工具函数
提供常用的测试辅助方法
"""
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.post import Post
from app.models.salary import SalaryRecord
from app.models.payday import PaydayConfig
from app.models.membership import Membership, MembershipOrder
from app.models.notification import Notification


class TestDataFactory:
    """测试数据工厂类"""

    @staticmethod
    async def create_user(
        db: AsyncSession,
        nickname: str = None,
        avatar: str = None,
        is_active: bool = True
    ) -> User:
        """创建测试用户"""
        user = User(
            openid=f"test_openid_{random.randint(1000, 9999)}",
            session_key=f"test_session_{random.randint(1000, 9999)}",
            nickname=nickname or f"测试用户{random.randint(1000, 9999)}",
            avatar=avatar or "https://example.com/avatar.jpg",
            is_active=is_active,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def create_post(
        db: AsyncSession,
        user_id: str,
        content: str = None,
        mood: str = "happy",
        is_anonymous: bool = False
    ) -> Post:
        """创建测试帖子"""
        post = Post(
            user_id=user_id,
            content=content or f"这是一条测试帖子 {random.randint(1000, 9999)}",
            images=[],
            mood=mood,
            is_anonymous=is_anonymous,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    @staticmethod
    async def create_salary(
        db: AsyncSession,
        user_id: str,
        config_id: str,
        amount: int = 15000,
        mood: str = "happy"
    ) -> SalaryRecord:
        """创建测试薪资记录"""
        salary = SalaryRecord(
            user_id=user_id,
            config_id=config_id,
            amount=amount,
            actual_payday=datetime.now().date(),
            mood=mood,
            is_public=False,
        )
        db.add(salary)
        await db.commit()
        await db.refresh(salary)
        return salary

    @staticmethod
    async def create_payday_config(
        db: AsyncSession,
        user_id: str,
        job_name: str = None,
        payday: int = 25
    ) -> PaydayConfig:
        """创建测试发薪日配置"""
        config = PaydayConfig(
            user_id=user_id,
            job_name=job_name or f"测试工作{random.randint(1000, 9999)}",
            payday=payday,
            is_monthly=True,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def create_membership(
        db: AsyncSession,
        name: str = None,
        level: int = 1,
        price: int = 9900,
        duration_days: int = 30
    ) -> Membership:
        """创建测试会员套餐"""
        membership = Membership(
            name=name or f"测试会员{random.randint(1000, 9999)}",
            level=level,
            price=price,
            duration_days=duration_days,
            benefits={"posts_per_day": 10, "advanced_stats": True},
            is_active=True,
        )
        db.add(membership)
        await db.commit()
        await db.refresh(membership)
        return membership

    @staticmethod
    async def create_order(
        db: AsyncSession,
        user_id: str,
        membership_id: str,
        status: str = "pending"
    ) -> MembershipOrder:
        """创建测试订单"""
        order = MembershipOrder(
            user_id=user_id,
            membership_id=membership_id,
            order_id=f"TEST_ORDER_{random.randint(100000, 999999)}",
            amount=9900,
            status=status,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def create_comment(
        db: AsyncSession,
        user_id: str,
        post_id: str,
        content: str = None
    ) -> Any:
        """创建测试评论"""
        from app.models.comment import Comment

        comment = Comment(
            user_id=user_id,
            post_id=post_id,
            content=content or f"测试评论 {random.randint(1000, 9999)}",
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: str,
        type: str = "like",
        content: str = None
    ) -> Notification:
        """创建测试通知"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title="测试通知",
            content=content or "这是一条测试通知",
            is_read=False,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification


def random_string(length: int = 10) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_email() -> str:
    """生成随机邮箱地址"""
    return f"test_{random.randint(1000, 9999)}@example.com"


def random_phone() -> str:
    """生成随机手机号码"""
    return f"1{random.choice([3, 5, 7, 8, 9])}{random.randint(100000000, 999999999)}"


def future_date(days: int = 7) -> datetime:
    """获取未来日期"""
    return datetime.now() + timedelta(days=days)


def past_date(days: int = 7) -> datetime:
    """获取过去日期"""
    return datetime.now() - timedelta(days=days)


def assert_valid_id(id_value: Any) -> bool:
    """验证 ID 格式"""
    return id_value is not None and str(id_value).strip() != ""


def assert_response_shape(
    response: dict,
    required_keys: list[str],
    exclude_keys: list[str] = None
) -> None:
    """验证响应数据结构"""
    for key in required_keys:
        assert key in response, f"响应缺少必需字段: {key}"

    if exclude_keys:
        for key in exclude_keys:
            assert key not in response, f"响应不应包含字段: {key}"


async def assert_async_raises(
    coroutine,
    expected_exception: Exception,
    message_match: str = None
):
    """断言异步函数抛出特定异常"""
    try:
        await coroutine
        raise AssertionError(f"期望抛出 {expected_exception.__name__} 异常")
    except expected_exception as e:
        if message_match:
            assert message_match in str(e), f"异常消息不匹配: {str(e)}"
    except Exception as e:
        raise AssertionError(f"抛出了错误的异常类型: {type(e).__name__}")


class MockDateTime:
    """Mock datetime 工具"""

    def __init__(self, target_datetime: datetime):
        self.target_datetime = target_datetime
        self.original_datetime = datetime

    def __enter__(self):
        # 替换 datetime
        import sys
        sys.modules['datetime'] = type(
            'datetime',
            (),
            {
                'datetime': self.target_datetime,
                'date': self.target_datetime.date(),
                'now': lambda: self.target_datetime,
            }
        )()
        return self

    def __exit__(self, *args):
        # 恢复原始 datetime
        import sys
        sys.modules['datetime'] = self.original_datetime
