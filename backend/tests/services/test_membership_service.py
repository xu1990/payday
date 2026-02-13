"""
单元测试 - 会员服务 (app.services.membership_service)
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership, MembershipOrder
from app.services.membership_service import (
    list_memberships,
    create_order,
    get_my_orders,
    get_active_membership,
    verify_membership_benefits,
    cancel_order,
)
from app.core.exceptions import BusinessException, NotFoundException
from app.schemas.membership import MembershipOrderCreate


@pytest.mark.asyncio
class TestListMemberships:
    """测试获取会员套餐列表"""

    async def test_list_empty_memberships(self, db_session: AsyncSession):
        """测试空列表"""
        result = await list_memberships(db_session)
        assert result == []

    async def test_list_active_memberships_only(self, db_session: AsyncSession):
        """测试只返回启用的套餐"""
        # 创建启用的套餐
        active1 = Membership(
            name="基础会员",
            description="基础会员套餐",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        active2 = Membership(
            name="高级会员",
            description="高级会员套餐",
            price=200,
            duration_days=90,
            is_active=True,
            sort_order=2,
        )
        # 创建禁用的套餐
        inactive = Membership(
            name="禁用会员",
            description="禁用会员套餐",
            price=300,
            duration_days=180,
            is_active=False,
            sort_order=3,
        )

        db_session.add(active1)
        db_session.add(active2)
        db_session.add(inactive)
        await db_session.commit()

        result = await list_memberships(db_session)

        # 应该只返回启用的套餐
        assert len(result) == 2
        names = {m.name for m in result}
        assert "基础会员" in names
        assert "高级会员" in names
        assert "禁用会员" not in names

    async def test_list_sorted_by_sort_order_and_price(self, db_session: AsyncSession):
        """测试排序：按sort_order和price排序"""
        m1 = Membership(name="会员1", price=100, duration_days=30, is_active=True, sort_order=2)
        m2 = Membership(name="会员2", price=200, duration_days=30, is_active=True, sort_order=1)
        m3 = Membership(name="会员3", price=150, duration_days=30, is_active=True, sort_order=1)

        db_session.add(m1)
        db_session.add(m2)
        db_session.add(m3)
        await db_session.commit()

        result = await list_memberships(db_session)

        # sort_order=1 的应该在前，同 sort_order 的按 price 排序
        assert result[0].sort_order == 1
        assert result[0].price <= result[1].price if result[1].sort_order == 1 else True


@pytest.mark.asyncio
class TestCreateOrder:
    """测试创建会员订单"""

    async def test_create_order_success(self, db_session: AsyncSession):
        """测试成功创建订单"""
        # 创建套餐
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        # 创建订单
        order = await create_order(
            db_session,
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
            payment_method="wechat",
        )

        assert order.id is not None
        assert order.user_id == "test_user_id"
        assert order.membership_id == membership.id
        assert order.amount == 100
        assert order.status == "pending"
        assert order.payment_method == "wechat"
        assert order.start_date is not None
        assert order.end_date is not None

    async def test_create_order_calculates_dates(self, db_session: AsyncSession):
        """测试正确计算起止日期"""
        membership = Membership(
            name="30天会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        order = await create_order(
            db_session,
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
        )

        today = datetime.utcnow().date()

        # DateTime 列存储的是 datetime，比较 date 部分
        assert order.start_date.date() == today
        expected_end = today + timedelta(days=30)
        assert order.end_date.date() == expected_end

    async def test_create_order_idempotent_check(self, db_session: AsyncSession):
        """测试幂等性检查：防止重复pending订单"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        # 创建第一个订单
        await create_order(
            db_session,
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
        )

        # 尝试创建第二个订单（应该失败）
        with pytest.raises(BusinessException) as exc_info:
            await create_order(
                db_session,
                user_id="test_user_id",
                membership_id=membership.id,
                amount=100,
            )

        assert "已有pending订单" in str(exc_info.value)

    async def test_create_order_nonexistent_membership(self, db_session: AsyncSession):
        """测试不存在的套餐"""
        with pytest.raises(NotFoundException) as exc_info:
            await create_order(
                db_session,
                user_id="test_user_id",
                membership_id="nonexistent_id",
                amount=100,
            )

        assert "不存在" in str(exc_info.value)

    async def test_create_order_inactive_membership(self, db_session: AsyncSession):
        """测试禁用的套餐"""
        membership = Membership(
            name="禁用会员",
            price=100,
            duration_days=30,
            is_active=False,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        with pytest.raises(BusinessException) as exc_info:
            await create_order(
                db_session,
                user_id="test_user_id",
                membership_id=membership.id,
                amount=100,
            )

        assert "未启用" in str(exc_info.value)

    async def test_create_order_with_transaction_id(self, db_session: AsyncSession):
        """测试带交易ID的订单"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        order = await create_order(
            db_session,
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
            transaction_id="txn_12345",
        )

        assert order.transaction_id == "txn_12345"


@pytest.mark.asyncio
class TestGetMyOrders:
    """测试获取我的订单"""

    async def test_get_empty_orders(self, db_session: AsyncSession):
        """测试空订单列表"""
        result = await get_my_orders(db_session, user_id="test_user_id")
        assert result == []

    async def test_get_my_orders_only(self, db_session: AsyncSession):
        """测试只返回自己的订单"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        # 创建自己的订单
        order1 = MembershipOrder(
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
            status="pending",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
        )
        # 创建其他人的订单
        order2 = MembershipOrder(
            user_id="other_user_id",
            membership_id=membership.id,
            amount=100,
            status="pending",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
        )

        db_session.add(order1)
        db_session.add(order2)
        await db_session.commit()

        result = await get_my_orders(db_session, user_id="test_user_id")

        assert len(result) == 1
        assert result[0].user_id == "test_user_id"

    async def test_get_orders_sorted_by_created_at_desc(self, db_session: AsyncSession):
        """测试按创建时间倒序排列"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        # 创建多个订单
        for i in range(3):
            order = MembershipOrder(
                user_id="test_user_id",
                membership_id=membership.id,
                amount=100,
                status="pending",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30),
            )
            db_session.add(order)
            await db_session.commit()

        result = await get_my_orders(db_session, user_id="test_user_id")

        # 最新的应该在前面
        assert len(result) == 3
        assert result[0].created_at >= result[1].created_at
        assert result[1].created_at >= result[2].created_at


@pytest.mark.asyncio
class TestGetActiveMembership:
    """测试获取激活会员"""

    async def test_no_active_membership_returns_none(self, db_session: AsyncSession):
        """测试没有激活会员返回None"""
        result = await get_active_membership(db_session, user_id="test_user_id")
        assert result is None

    async def test_paid_order_is_active(self, db_session: AsyncSession):
        """测试已支付订单算激活"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        # 创建已支付订单
        order = MembershipOrder(
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
            status="paid",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(order)
        await db_session.commit()

        result = await get_active_membership(db_session, user_id="test_user_id")

        assert result is not None
        assert result["name"] == "基础会员"
        assert "end_date" in result
        assert "days_remaining" in result

    async def test_expired_order_not_active(self, db_session: AsyncSession):
        """测试过期订单不算激活"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        # 创建过期订单
        order = MembershipOrder(
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
            status="paid",
            start_date=datetime.utcnow() - timedelta(days=60),
            end_date=datetime.utcnow() - timedelta(days=1),
        )
        db_session.add(order)
        await db_session.commit()

        result = await get_active_membership(db_session, user_id="test_user_id")

        assert result is None

    async def test_pending_order_not_active(self, db_session: AsyncSession):
        """测试pending订单不算激活"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        order = MembershipOrder(
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
            status="pending",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(order)
        await db_session.commit()

        result = await get_active_membership(db_session, user_id="test_user_id")

        assert result is None


@pytest.mark.asyncio
class TestVerifyMembershipBenefits:
    """测试会员权益验证"""

    async def test_no_membership_returns_false(self, db_session: AsyncSession):
        """测试没有会员返回False"""
        result = await verify_membership_benefits(db_session, user_id="test_user_id", endpoint="some_feature")
        assert result is False

    async def test_active_membership_returns_true(self, db_session: AsyncSession):
        """测试激活会员返回True"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        order = MembershipOrder(
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
            status="paid",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(order)
        await db_session.commit()

        result = await verify_membership_benefits(db_session, user_id="test_user_id", endpoint="some_feature")

        assert result is True


@pytest.mark.asyncio
class TestCancelOrder:
    """测试取消订单"""

    async def test_cancel_pending_order_success(self, db_session: AsyncSession):
        """测试取消pending订单成功"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        order = MembershipOrder(
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
            status="pending",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(order)
        await db_session.commit()

        result = await cancel_order(db_session, order_id=order.id, user_id="test_user_id")

        assert result is True

        # 验证状态已更新
        await db_session.refresh(order)
        assert order.status == "cancelled"

    async def test_cancel_nonexistent_order(self, db_session: AsyncSession):
        """测试取消不存在的订单"""
        with pytest.raises(NotFoundException) as exc_info:
            await cancel_order(db_session, order_id="nonexistent_id", user_id="test_user_id")

        assert "不存在" in str(exc_info.value)

    async def test_cancel_paid_order_fails(self, db_session: AsyncSession):
        """测试不能取消已支付订单"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        order = MembershipOrder(
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
            status="paid",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(order)
        await db_session.commit()

        with pytest.raises(BusinessException) as exc_info:
            await cancel_order(db_session, order_id=order.id, user_id="test_user_id")

        assert "无法取消" in str(exc_info.value)

    async def test_cancel_other_users_order_fails(self, db_session: AsyncSession):
        """测试不能取消其他人的订单"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        order = MembershipOrder(
            user_id="other_user_id",
            membership_id=membership.id,
            amount=100,
            status="pending",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(order)
        await db_session.commit()

        # 尝试用test_user_id取消other_user_id的订单
        with pytest.raises(NotFoundException):
            await cancel_order(db_session, order_id=order.id, user_id="test_user_id")

    async def test_cancel_already_cancelled_order(self, db_session: AsyncSession):
        """测试取消已取消的订单"""
        membership = Membership(
            name="基础会员",
            price=100,
            duration_days=30,
            is_active=True,
            sort_order=1,
        )
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)

        order = MembershipOrder(
            user_id="test_user_id",
            membership_id=membership.id,
            amount=100,
            status="cancelled",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(order)
        await db_session.commit()

        with pytest.raises(BusinessException) as exc_info:
            await cancel_order(db_session, order_id=order.id, user_id="test_user_id")

        assert "无法取消" in str(exc_info.value)
