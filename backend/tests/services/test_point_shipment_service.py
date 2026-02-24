"""
Point Shipment Service 测试 - 积分订单物流服务

测试覆盖：
1. create_shipment - 创建发货记录（成功、订单不存在、订单未支付、已发货）
2. list_shipments - 获取发货列表（成功、空列表、分页）
3. get_shipment - 获取发货记录（成功、不存在）
4. update_shipment - 更新发货记录（成功、不存在、状态无效）
5. get_tracking_info - 获取物流跟踪信息（成功、不存在）
6. 业务逻辑验证（订单所有权、状态检查、权限控制）
7. 错误处理和异常场景
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.point_shipment_service import PointShipmentService
from app.models.order import Order, OrderItem
from app.models.shipping import OrderShipment, CourierCompany
from app.models.user import User
from app.core.exceptions import NotFoundException, BusinessException, ValidationException


class TestCreateShipment:
    """测试创建发货记录"""

    @pytest.mark.asyncio
    async def test_create_shipment_success(self, db_session: AsyncSession):
        """测试创建发货成功"""
        # Create test user and order
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()
        shipment = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        assert shipment is not None
        assert shipment.order_id == order.id
        assert shipment.courier_code == courier.code
        assert shipment.tracking_number == "SF1234567890"
        assert shipment.status == "pending"
        assert shipment.shipped_at is not None

    @pytest.mark.asyncio
    async def test_create_shipment_order_not_found(self, db_session: AsyncSession):
        """测试订单不存在"""
        service = PointShipmentService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.create_shipment(
                db=db_session,
                order_id="nonexistent_order",
                courier_code="SF",
                tracking_number="SF1234567890"
            )

        assert "订单不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_shipment_order_not_paid(self, db_session: AsyncSession):
        """测试订单未支付不能发货"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="pending", payment_method="points")

        service = PointShipmentService()

        with pytest.raises(BusinessException) as exc_info:
            await service.create_shipment(
                db=db_session,
                order_id=order.id,
                courier_code="SF",
                tracking_number="SF1234567890"
            )

        assert "订单未支付" in str(exc_info.value)
        assert exc_info.value.code == "ORDER_NOT_PAID"

    @pytest.mark.asyncio
    async def test_create_shipment_already_shipped(self, db_session: AsyncSession):
        """测试订单已发货不能重复发货"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()

        # First shipment
        await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        # Try to ship again
        with pytest.raises(BusinessException) as exc_info:
            await service.create_shipment(
                db=db_session,
                order_id=order.id,
                courier_code=courier.code,
                tracking_number="SF1234567891"
            )

        assert "订单已发货" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_shipment_cash_order_forbidden(self, db_session: AsyncSession):
        """测试现金订单不能通过积分订单物流服务发货"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid", payment_method="wechat")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()

        with pytest.raises(BusinessException) as exc_info:
            await service.create_shipment(
                db=db_session,
                order_id=order.id,
                courier_code=courier.code,
                tracking_number="SF1234567890"
            )

        assert "该订单类型不能使用积分订单物流服务" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_shipment_updates_order_status(self, db_session: AsyncSession):
        """测试创建发货后更新订单状态为shipped"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()
        await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        # Refresh order from database
        await db_session.refresh(order)
        assert order.status == "shipped"

    @pytest.mark.asyncio
    async def test_create_shipment_courier_not_found(self, db_session: AsyncSession):
        """测试物流公司不存在"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid", payment_method="points")

        service = PointShipmentService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.create_shipment(
                db=db_session,
                order_id=order.id,
                courier_code="NONEXISTENT",
                tracking_number="SF1234567890"
            )

        assert "物流公司不存在" in str(exc_info.value)


class TestListShipments:
    """测试获取发货列表"""

    @pytest.mark.asyncio
    async def test_list_shipments_success(self, db_session: AsyncSession):
        """测试获取发货列表成功"""
        user = await _create_test_user(db_session)
        order1 = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        order2 = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()

        # Create shipments
        await service.create_shipment(
            db=db_session,
            order_id=order1.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )
        await service.create_shipment(
            db=db_session,
            order_id=order2.id,
            courier_code=courier.code,
            tracking_number="SF1234567891"
        )

        # List shipments
        shipments = await service.list_shipments(db=db_session, skip=0, limit=10)

        assert len(shipments) >= 2
        assert all(shipment.status in ["pending", "picked_up", "in_transit"] for shipment in shipments)

    @pytest.mark.asyncio
    async def test_list_shipments_empty(self, db_session: AsyncSession):
        """测试获取发货列表为空"""
        service = PointShipmentService()

        shipments = await service.list_shipments(db=db_session, skip=0, limit=10)

        assert len(shipments) == 0

    @pytest.mark.asyncio
    async def test_list_shipments_with_filters(self, db_session: AsyncSession):
        """测试带过滤条件的发货列表"""
        user = await _create_test_user(db_session)
        order1 = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        order2 = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()

        # Create shipments
        await service.create_shipment(
            db=db_session,
            order_id=order1.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )
        await service.create_shipment(
            db=db_session,
            order_id=order2.id,
            courier_code=courier.code,
            tracking_number="SF1234567891"
        )

        # Test status filter
        pending_shipments = await service.list_shipments(
            db=db_session,
            status="pending"
        )
        assert len(pending_shipments) >= 2

        # Test courier filter
        sf_shipments = await service.list_shipments(
            db=db_session,
            courier_code=courier.code
        )
        assert len(sf_shipments) >= 2

    @pytest.mark.asyncio
    async def test_list_shipments_with_pagination(self, db_session: AsyncSession):
        """测试分页查询"""
        user = await _create_test_user(db_session)

        # Create multiple orders
        orders = []
        for i in range(5):
            order = await _create_test_order(
                db_session,
                user.id,
                status="paid",
                payment_method="points"
            )
            orders.append(order)

        courier = await _create_test_courier(db_session)

        service = PointShipmentService()

        # Create all shipments
        for i, order in enumerate(orders):
            await service.create_shipment(
                db=db_session,
                order_id=order.id,
                courier_code=courier.code,
                tracking_number=f"SF12345678{i}"
            )

        # Test pagination
        page1 = await service.list_shipments(db=db_session, skip=0, limit=2)
        page2 = await service.list_shipments(db=db_session, skip=2, limit=2)

        assert len(page1) == 2
        assert len(page2) >= 2


class TestGetShipment:
    """测试获取发货记录"""

    @pytest.mark.asyncio
    async def test_get_shipment_success(self, db_session: AsyncSession):
        """测试获取发货记录成功"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()
        created = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        shipment = await service.get_shipment(db=db_session, shipment_id=created.id)

        assert shipment is not None
        assert shipment.id == created.id
        assert shipment.tracking_number == "SF1234567890"

    @pytest.mark.asyncio
    async def test_get_shipment_not_found(self, db_session: AsyncSession):
        """测试发货记录不存在"""
        service = PointShipmentService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.get_shipment(db=db_session, shipment_id="nonexistent_shipment")

        assert "发货记录不存在" in str(exc_info.value)


class TestUpdateShipment:
    """测试更新发货记录"""

    @pytest.mark.asyncio
    async def test_update_shipment_success(self, db_session: AsyncSession):
        """测试更新发货记录成功"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()
        created = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        updated = await service.update_shipment(
            db=db_session,
            shipment_id=created.id,
            tracking_number="SF1234567891",
            status="picked_up"
        )

        assert updated.tracking_number == "SF1234567891"
        assert updated.status == "picked_up"

    @pytest.mark.asyncio
    async def test_update_shipment_not_found(self, db_session: AsyncSession):
        """测试发货记录不存在"""
        service = PointShipmentService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.update_shipment(
                db=db_session,
                shipment_id="nonexistent_shipment",
                tracking_number="SF1234567891",
                status="picked_up"
            )

        assert "发货记录不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_shipment_invalid_status(self, db_session: AsyncSession):
        """测试无效的状态"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()
        created = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        with pytest.raises(ValidationException) as exc_info:
            await service.update_shipment(
                db=db_session,
                shipment_id=created.id,
                tracking_number="SF1234567891",
                status="invalid_status"
            )

        assert "无效的物流状态" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_shipment_updates_order_status(self, db_session: AsyncSession):
        """测试更新发货状态为已签收后更新订单状态"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="shipped", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()
        shipment = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        await service.update_shipment(
            db=db_session,
            shipment_id=shipment.id,
            tracking_number="SF1234567890",
            status="delivered"
        )

        await db_session.refresh(order)
        assert order.status == "delivered"


class TestGetTrackingInfo:
    """测试获取物流跟踪信息"""

    @pytest.mark.asyncio
    async def test_get_tracking_info_success(self, db_session: AsyncSession):
        """测试获取物流跟踪信息成功"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()
        created = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        # Update with tracking info
        tracking_info = [
            {"time": "2024-02-24 10:00", "status": "已揽收", "location": "深圳市"},
            {"time": "2024-02-24 15:00", "status": "运输中", "location": "广州市"}
        ]

        await service.update_shipment(
            db=db_session,
            shipment_id=created.id,
            tracking_number="SF1234567890",
            status="in_transit",
            tracking_info=tracking_info
        )

        tracking = await service.get_tracking_info(db=db_session, shipment_id=created.id)

        assert tracking is not None
        assert len(tracking) == 2
        assert tracking[0]["status"] == "已揽收"
        assert tracking[1]["status"] == "运输中"

    @pytest.mark.asyncio
    async def test_get_tracking_info_empty(self, db_session: AsyncSession):
        """测试获取物流跟踪信息为空"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid", payment_method="points")
        courier = await _create_test_courier(db_session)

        service = PointShipmentService()
        created = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        # Fresh shipment without tracking info
        tracking = await service.get_tracking_info(db=db_session, shipment_id=created.id)

        assert tracking == []

    @pytest.mark.asyncio
    async def test_get_tracking_info_not_found(self, db_session: AsyncSession):
        """测试发货记录不存在"""
        service = PointShipmentService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.get_tracking_info(db=db_session, shipment_id="nonexistent_shipment")

        assert "发货记录不存在" in str(exc_info.value)


# Helper functions (module-level, accessible by all test classes)
async def _create_test_user(db: AsyncSession) -> User:
    """创建测试用户"""
    import uuid
    user = User(
        id=f"user_{uuid.uuid4().hex}",
        openid=f"openid_{uuid.uuid4().hex}",
        anonymous_name="测试用户",
        status="normal"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_test_admin(db: AsyncSession):
    """创建测试管理员"""
    from app.models.admin import AdminUser
    from app.core.security import hash_password
    import uuid

    admin = AdminUser(
        id=f"admin_{uuid.uuid4().hex}",
        username="test_admin",
        password_hash=hash_password("password"),
        role="admin"
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def _create_test_order(db: AsyncSession, user_id: str, status: str = "paid", payment_method: str = "points", final_amount: int = 10000) -> Order:
    """创建测试订单"""
    import uuid
    order = Order(
        id=f"order_{uuid.uuid4().hex}",
        user_id=user_id,
        order_number=f"ORD{datetime.now().strftime('%Y%m%d')}000001",
        total_amount=Decimal(str(final_amount)),
        points_used=payment_method == "points" and final_amount or 0,
        discount_amount=Decimal("0"),
        shipping_cost=Decimal("0"),
        final_amount=Decimal(str(final_amount)),
        payment_method=payment_method,
        payment_status="paid" if status in ["paid", "shipped", "delivered"] else "pending",
        status=status,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    if status == "paid":
        order.paid_at = datetime.utcnow()
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def _create_test_order_item(db: AsyncSession, order_id: str, subtotal: int = 10000) -> OrderItem:
    """创建测试订单项"""
    import uuid
    item = OrderItem(
        id=f"item_{uuid.uuid4().hex}",
        order_id=order_id,
        product_id=f"product_{uuid.uuid4().hex}",
        sku_id=f"sku_{uuid.uuid4().hex}",
        product_name="测试商品",
        sku_name="红色-L码",
        product_image="image.jpg",
        unit_price=Decimal(str(subtotal)),
        quantity=1,
        subtotal=Decimal(str(subtotal))
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def _create_test_courier(db: AsyncSession) -> CourierCompany:
    """创建测试物流公司"""
    import uuid
    courier = CourierCompany(
        id=f"courier_{uuid.uuid4().hex}",
        code="SF",
        name="顺丰速运",
        website="https://www.sf-express.com",
        tracking_url="https://www.sf-express.com/search",
        is_active=True
    )
    db.add(courier)
    await db.commit()
    await db.refresh(courier)
    return courier