"""会员API测试"""
import pytest
from datetime import datetime, timedelta
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.membership import Membership, MembershipOrder
from app.schemas.membership import MembershipOrderCreate


async def create_test_membership(db: AsyncSession, name: str, price: float, days: int) -> Membership:
    """Helper function to create a test membership"""
    membership = Membership(
        name=name,
        description=f"{name}套餐",
        price=price,
        duration_days=days,
        is_active=1,
        sort_order=0,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


async def create_test_order(
    db: AsyncSession, user_id: str, membership_id: str, order_status: str = "pending"
) -> MembershipOrder:
    """Helper function to create a test order"""
    start_date = datetime.utcnow().date()
    end_date = start_date + timedelta(days=30)

    order = MembershipOrder(
        user_id=user_id,
        membership_id=membership_id,
        amount=100,
        status=order_status,
        payment_method="wechat",
        start_date=start_date,
        end_date=end_date,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@pytest.mark.asyncio
class TestListMembershipsEndpoint:
    """测试获取会员套餐列表接口"""

    async def test_list_memberships_empty(self, client, user_headers: dict):
        """测试空列表"""
        response = client.get("/api/v1/membership", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert data["items"] == []

    async def test_list_memberships_with_data(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试有套餐的列表"""
        # 创建两个套餐
        await create_test_membership(db_session, "基础会员", 100, 30)
        await create_test_membership(db_session, "高级会员", 200, 90)
        await db_session.commit()

        response = client.get("/api/v1/membership", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] in ["基础会员", "高级会员"]

    async def test_list_memberships_only_active(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试只返回启用的套餐"""
        # 创建启用和禁用的套餐
        active = await create_test_membership(db_session, "启用套餐", 100, 30)

        inactive = await create_test_membership(db_session, "禁用套餐", 200, 90)
        inactive.is_active = 0
        await db_session.commit()

        response = client.get("/api/v1/membership", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        items = data["items"]
        # 只应返回启用的套餐
        assert any(t["id"] == active.id for t in items)
        assert not any(t["id"] == inactive.id for t in items)

    async def test_list_memberships_response_format(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试返回正确的数据格式"""
        await create_test_membership(db_session, "测试套餐", 100, 30)

        response = client.get("/api/v1/membership", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        item = data["items"][0]
        # 验证所有字段存在
        assert "id" in item
        assert "name" in item
        assert "description" in item
        assert "price" in item
        assert "duration_days" in item
        assert "is_active" in item
        # 验证数据类型
        assert isinstance(item["price"], float)
        assert isinstance(item["duration_days"], int)
        assert isinstance(item["is_active"], bool)

    async def test_list_requires_auth(self, client):
        """测试需要认证"""
        response = client.get("/api/v1/membership")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestCreateOrderEndpoint:
    """测试创建会员订单接口"""

    async def test_create_order_success(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试成功创建订单"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)

        response = client.post(
            "/api/v1/membership/order",
            json={
                "membership_id": membership.id,
                "amount": 100,
                "payment_method": "wechat",
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "pending"
        assert data["message"] == "订单创建成功"
        assert "id" in data

    async def test_create_order_with_minimal_fields(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试仅提供必填字段"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)

        response = client.post(
            "/api/v1/membership/order",
            json={
                "membership_id": membership.id,
                "amount": 100,
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "pending"

    async def test_create_order_nonexistent_membership(
        self, client, test_user: User, user_headers: dict
    ):
        """测试创建不存在的套餐订单"""
        response = client.post(
            "/api/v1/membership/order",
            json={
                "membership_id": "nonexistent_id",
                "amount": 100,
            },
            headers=user_headers,
        )

        assert response.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST)

    async def test_create_order_duplicate_pending(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试重复创建pending订单"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        # 创建第一个pending订单
        await create_test_order(db_session, test_user.id, membership.id, "pending")

        # 尝试创建第二个订单
        response = client.post(
            "/api/v1/membership/order",
            json={
                "membership_id": membership.id,
                "amount": 100,
            },
            headers=user_headers,
        )

        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT)

    async def test_create_order_response_format(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试创建订单返回格式"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)

        response = client.post(
            "/api/v1/membership/order",
            json={
                "membership_id": membership.id,
                "amount": 100,
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert data["status"] == "pending"
        assert "message" in data

    async def test_create_order_with_payment_method(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试创建订单带支付方式"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)

        response = client.post(
            "/api/v1/membership/order",
            json={
                "membership_id": membership.id,
                "amount": 100,
                "payment_method": "alipay",
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_create_order_requires_auth(self, client):
        """测试需要认证"""
        response = client.post(
            "/api/v1/membership/order",
            json={"membership_id": "some_id", "amount": 100},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestListMyOrdersEndpoint:
    """测试获取我的订单列表接口"""

    async def test_list_empty_orders(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试空订单列表"""
        response = client.get("/api/v1/membership/my-orders", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert data["items"] == []

    async def test_list_orders_with_data(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试有订单的列表"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        # 创建两个订单
        await create_test_order(db_session, test_user.id, membership.id, "paid")
        await create_test_order(db_session, test_user.id, membership.id, "pending")

        response = client.get("/api/v1/membership/my-orders", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 2

    async def test_list_only_own_orders(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试只返回自己的订单"""
        # 创建另一个用户
        other_user_id = "other_user_id"

        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        # 创建其他用户的订单
        await create_test_order(db_session, other_user_id, membership.id, "paid")

        response = client.get("/api/v1/membership/my-orders", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 不应包含其他用户的订单
        assert len(data["items"]) == 0

    async def test_list_orders_response_format(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试订单列表返回格式"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        await create_test_order(db_session, test_user.id, membership.id, "paid")

        response = client.get("/api/v1/membership/my-orders", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        if len(data["items"]) > 0:
            order = data["items"][0]
            # 验证订单字段
            assert "id" in order
            assert "amount" in order
            assert "status" in order
            assert "payment_method" in order
            assert "start_date" in order
            assert "end_date" in order

    async def test_list_requires_auth(self, client):
        """测试需要认证"""
        response = client.get("/api/v1/membership/my-orders")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestGetActiveMembershipEndpoint:
    """测试获取激活会员接口"""

    async def test_get_no_active_membership(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试没有激活会员"""
        response = client.get("/api/v1/membership/active", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {}

    async def test_get_active_membership(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试获取激活会员"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        # 创建已支付订单
        await create_test_order(db_session, test_user.id, membership.id, "paid")

        response = client.get("/api/v1/membership/active", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert data["name"] == "基础会员"
        assert "end_date" in data
        assert "days_remaining" in data

    async def test_expired_order_not_active(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试过期订单不算激活"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)

        # 创建过期的已支付订单
        start_date = datetime.utcnow().date() - timedelta(days=60)
        end_date = datetime.utcnow().date() - timedelta(days=1)
        order = MembershipOrder(
            user_id=test_user.id,
            membership_id=membership.id,
            amount=100,
            status="paid",
            payment_method="wechat",
            start_date=start_date,
            end_date=end_date,
        )
        db_session.add(order)
        await db_session.commit()

        response = client.get("/api/v1/membership/active", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {}

    async def test_pending_order_not_active(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试pending订单不算激活"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        await create_test_order(db_session, test_user.id, membership.id, "pending")

        response = client.get("/api/v1/membership/active", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {}

    async def test_get_active_membership_response_format(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试激活会员返回格式"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        await create_test_order(db_session, test_user.id, membership.id, "paid")

        response = client.get("/api/v1/membership/active", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 验证返回的会员数据格式
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "end_date" in data
        assert "days_remaining" in data
        assert isinstance(data["days_remaining"], int)

    async def test_requires_auth(self, client):
        """测试需要认证"""
        response = client.get("/api/v1/membership/active")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestCancelOrderEndpoint:
    """测试取消订单接口"""

    async def test_cancel_pending_order(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试取消pending订单"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        order = await create_test_order(db_session, test_user.id, membership.id, "pending")

        response = client.post(f"/api/v1/membership/order/{order.id}/cancel", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "取消" in data["message"]

    async def test_cancel_nonexistent_order(
        self, client, test_user: User, user_headers: dict
    ):
        """测试取消不存在的订单"""
        response = client.post("/api/v1/membership/order/nonexistent_id/cancel", headers=user_headers)

        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)

    async def test_cancel_paid_order_fails(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试不能取消已支付订单"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        order = await create_test_order(db_session, test_user.id, membership.id, "paid")

        response = client.post(f"/api/v1/membership/order/{order.id}/cancel", headers=user_headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_cancel_other_users_order_fails(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试不能取消其他用户的订单"""
        # 创建另一个用户的订单
        other_user_id = "other_user_id"
        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        order = await create_test_order(db_session, other_user_id, membership.id, "pending")

        response = client.post(f"/api/v1/membership/order/{order.id}/cancel", headers=user_headers)

        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)

    async def test_cancel_order_response_format(
        self, client, test_user: User, user_headers: dict, db_session: AsyncSession
    ):
        """测试取消订单成功返回格式"""
        membership = await create_test_membership(db_session, "基础会员", 100, 30)
        order = await create_test_order(db_session, test_user.id, membership.id, "pending")

        response = client.post(f"/api/v1/membership/order/{order.id}/cancel", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "message" in data
        assert "取消" in data["message"]

    async def test_requires_auth(self, client):
        """测试需要认证"""
        response = client.post("/api/v1/membership/order/some_order_id/cancel")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
