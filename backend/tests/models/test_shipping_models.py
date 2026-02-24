"""
Tests for OrderShipment and OrderReturn models
"""
import pytest
from datetime import datetime
from sqlalchemy import select, func
from app.models.shipping import OrderShipment, OrderReturn
from app.models.user import User
from app.models.order import Order, OrderItem


@pytest.mark.asyncio
async def test_create_order_shipment_basic(db_session):
    """Test creating an order shipment with basic fields"""
    # Create user and order first
    user = User(
        id="user-ship-1",
        openid="wx-test-ship-1",
        anonymous_name="测试用户1"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ship-1",
        user_id="user-ship-1",
        order_number="ORD202502240001",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat",
        payment_status="paid",
        status="paid"
    )
    db_session.add(order)
    await db_session.flush()

    # Create shipment
    shipment = OrderShipment(
        id="shipment-1",
        order_id="order-ship-1",
        courier_code="SF",
        courier_name="顺丰速运",
        tracking_number="SF1234567890",
        status="pending",
        shipped_at=datetime.utcnow()
    )
    db_session.add(shipment)
    await db_session.commit()
    await db_session.refresh(shipment)

    assert shipment.id == "shipment-1"
    assert shipment.order_id == "order-ship-1"
    assert shipment.courier_code == "SF"
    assert shipment.courier_name == "顺丰速运"
    assert shipment.tracking_number == "SF1234567890"
    assert shipment.status == "pending"
    assert shipment.shipped_at is not None
    assert shipment.delivered_at is None
    assert shipment.tracking_info is None


@pytest.mark.asyncio
async def test_order_shipment_status_enum(db_session):
    """Test all shipment status enum values"""
    user = User(
        id="user-ship-2",
        openid="wx-test-ship-2",
        anonymous_name="测试用户2"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ship-2",
        user_id="user-ship-2",
        order_number="ORD202502240002",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    statuses = ["pending", "picked_up", "in_transit", "delivered", "failed"]
    for i, status in enumerate(statuses):
        shipment = OrderShipment(
            id=f"shipment-status-{i}",
            order_id="order-ship-2",
            courier_code="SF",
            courier_name="顺丰速运",
            tracking_number=f"SF123456789{i}",
            status=status,
            shipped_at=datetime.utcnow()
        )
        db_session.add(shipment)

    await db_session.commit()

    # Verify all statuses were created
    result = await db_session.execute(
        select(OrderShipment.status).where(OrderShipment.order_id == "order-ship-2")
    )
    stored_statuses = [row[0] for row in result]
    assert set(stored_statuses) == set(statuses)


@pytest.mark.asyncio
async def test_order_shipment_with_tracking_info(db_session):
    """Test order shipment with JSON tracking info"""
    user = User(
        id="user-ship-3",
        openid="wx-test-ship-3",
        anonymous_name="测试用户3"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ship-3",
        user_id="user-ship-3",
        order_number="ORD202502240003",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    # Create shipment with tracking info
    tracking_info = {
        "events": [
            {
                "time": "2025-02-24T10:00:00",
                "status": "picked_up",
                "description": "快递已揽收"
            },
            {
                "time": "2025-02-24T14:30:00",
                "status": "in_transit",
                "description": "运输中"
            }
        ],
        "estimated_delivery": "2025-02-25T18:00:00",
        "current_location": "北京转运中心"
    }

    shipment = OrderShipment(
        id="shipment-tracking-1",
        order_id="order-ship-3",
        courier_code="SF",
        courier_name="顺丰速运",
        tracking_number="SF9876543210",
        status="in_transit",
        shipped_at=datetime.utcnow(),
        tracking_info=tracking_info
    )
    db_session.add(shipment)
    await db_session.commit()
    await db_session.refresh(shipment)

    assert shipment.tracking_info is not None
    assert len(shipment.tracking_info["events"]) == 2
    assert shipment.tracking_info["estimated_delivery"] == "2025-02-25T18:00:00"
    assert shipment.tracking_info["current_location"] == "北京转运中心"


@pytest.mark.asyncio
async def test_order_shipment_with_delivery(db_session):
    """Test order shipment with delivery timestamp"""
    user = User(
        id="user-ship-4",
        openid="wx-test-ship-4",
        anonymous_name="测试用户4"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ship-4",
        user_id="user-ship-4",
        order_number="ORD202502240004",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    shipped_at = datetime.utcnow()
    delivered_at = datetime.utcnow()

    shipment = OrderShipment(
        id="shipment-delivered-1",
        order_id="order-ship-4",
        courier_code="SF",
        courier_name="顺丰速运",
        tracking_number="SF5555555555",
        status="delivered",
        shipped_at=shipped_at,
        delivered_at=delivered_at
    )
    db_session.add(shipment)
    await db_session.commit()
    await db_session.refresh(shipment)

    assert shipment.status == "delivered"
    assert shipment.shipped_at is not None
    assert shipment.delivered_at is not None


@pytest.mark.asyncio
async def test_create_order_return_basic(db_session):
    """Test creating an order return with basic fields"""
    user = User(
        id="user-ret-1",
        openid="wx-test-ret-1",
        anonymous_name="测试用户5"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ret-1",
        user_id="user-ret-1",
        order_number="ORD202502240005",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        id="item-ret-1",
        order_id="order-ret-1",
        product_id="product-1",
        product_name="T恤",
        unit_price=5000,
        quantity=2,
        subtotal=10000
    )
    db_session.add(order_item)
    await db_session.flush()

    # Create return request
    return_request = OrderReturn(
        id="return-1",
        order_id="order-ret-1",
        order_item_id="item-ret-1",
        return_reason="quality_issue",
        return_description="衣服有破损",
        return_type="refund_only",
        status="requested"
    )
    db_session.add(return_request)
    await db_session.commit()
    await db_session.refresh(return_request)

    assert return_request.id == "return-1"
    assert return_request.order_id == "order-ret-1"
    assert return_request.order_item_id == "item-ret-1"
    assert return_request.return_reason == "quality_issue"
    assert return_request.return_description == "衣服有破损"
    assert return_request.return_type == "refund_only"
    assert return_request.status == "requested"
    assert return_request.refund_amount is None
    assert return_request.refund_transaction_id is None
    assert return_request.requested_at is not None


@pytest.mark.asyncio
async def test_order_return_reason_enum(db_session):
    """Test all return reason enum values"""
    user = User(
        id="user-ret-2",
        openid="wx-test-ret-2",
        anonymous_name="测试用户6"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ret-2",
        user_id="user-ret-2",
        order_number="ORD202502240006",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        id="item-ret-2",
        order_id="order-ret-2",
        product_id="product-1",
        product_name="T恤",
        unit_price=5000,
        quantity=2,
        subtotal=10000
    )
    db_session.add(order_item)
    await db_session.flush()

    reasons = [
        "quality_issue",
        "damaged",
        "wrong_item",
        "not_as_described",
        "no_longer_needed",
        "other"
    ]

    for i, reason in enumerate(reasons):
        return_request = OrderReturn(
            id=f"return-reason-{i}",
            order_id="order-ret-2",
            order_item_id="item-ret-2",
            return_reason=reason,
            return_type="refund_only",
            status="requested"
        )
        db_session.add(return_request)

    await db_session.commit()

    # Verify all reasons were created
    result = await db_session.execute(
        select(OrderReturn.return_reason).where(OrderReturn.order_id == "order-ret-2")
    )
    stored_reasons = [row[0] for row in result]
    assert set(stored_reasons) == set(reasons)


@pytest.mark.asyncio
async def test_order_return_type_enum(db_session):
    """Test all return type enum values"""
    user = User(
        id="user-ret-3",
        openid="wx-test-ret-3",
        anonymous_name="测试用户7"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ret-3",
        user_id="user-ret-3",
        order_number="ORD202502240007",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        id="item-ret-3",
        order_id="order-ret-3",
        product_id="product-1",
        product_name="T恤",
        unit_price=5000,
        quantity=2,
        subtotal=10000
    )
    db_session.add(order_item)
    await db_session.flush()

    return_types = ["refund_only", "replace", "return_and_refund"]

    for i, return_type in enumerate(return_types):
        return_request = OrderReturn(
            id=f"return-type-{i}",
            order_id="order-ret-3",
            order_item_id="item-ret-3",
            return_reason="quality_issue",
            return_type=return_type,
            status="requested"
        )
        db_session.add(return_request)

    await db_session.commit()

    # Verify all types were created
    result = await db_session.execute(
        select(OrderReturn.return_type).where(OrderReturn.order_id == "order-ret-3")
    )
    stored_types = [row[0] for row in result]
    assert set(stored_types) == set(return_types)


@pytest.mark.asyncio
async def test_order_return_status_enum(db_session):
    """Test all return status enum values"""
    user = User(
        id="user-ret-4",
        openid="wx-test-ret-4",
        anonymous_name="测试用户8"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ret-4",
        user_id="user-ret-4",
        order_number="ORD202502240008",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        id="item-ret-4",
        order_id="order-ret-4",
        product_id="product-1",
        product_name="T恤",
        unit_price=5000,
        quantity=2,
        subtotal=10000
    )
    db_session.add(order_item)
    await db_session.flush()

    statuses = [
        "requested", "approved", "rejected", "shipped_back",
        "received", "processing", "completed"
    ]

    for i, status in enumerate(statuses):
        return_request = OrderReturn(
            id=f"return-status-{i}",
            order_id="order-ret-4",
            order_item_id="item-ret-4",
            return_reason="quality_issue",
            return_type="refund_only",
            status=status
        )
        db_session.add(return_request)

    await db_session.commit()

    # Verify all statuses were created
    result = await db_session.execute(
        select(OrderReturn.status).where(OrderReturn.order_id == "order-ret-4")
    )
    stored_statuses = [row[0] for row in result]
    assert set(stored_statuses) == set(statuses)


@pytest.mark.asyncio
async def test_order_return_with_images(db_session):
    """Test order return with JSON images field"""
    user = User(
        id="user-ret-5",
        openid="wx-test-ret-5",
        anonymous_name="测试用户9"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ret-5",
        user_id="user-ret-5",
        order_number="ORD202502240009",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        id="item-ret-5",
        order_id="order-ret-5",
        product_id="product-1",
        product_name="T恤",
        unit_price=5000,
        quantity=2,
        subtotal=10000
    )
    db_session.add(order_item)
    await db_session.flush()

    # Create return with images
    images = [
        {
            "url": "https://example.com/image1.jpg",
            "description": "破损处特写"
        },
        {
            "url": "https://example.com/image2.jpg",
            "description": "整体照片"
        }
    ]

    return_request = OrderReturn(
        id="return-images-1",
        order_id="order-ret-5",
        order_item_id="item-ret-5",
        return_reason="damaged",
        return_description="包装破损",
        images=images,
        return_type="refund_only",
        status="requested"
    )
    db_session.add(return_request)
    await db_session.commit()
    await db_session.refresh(return_request)

    assert return_request.images is not None
    assert len(return_request.images) == 2
    assert return_request.images[0]["url"] == "https://example.com/image1.jpg"
    assert return_request.images[1]["description"] == "整体照片"


@pytest.mark.asyncio
async def test_order_return_with_refund(db_session):
    """Test order return with refund information"""
    user = User(
        id="user-ret-6",
        openid="wx-test-ret-6",
        anonymous_name="测试用户10"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ret-6",
        user_id="user-ret-6",
        order_number="ORD202502240010",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        id="item-ret-6",
        order_id="order-ret-6",
        product_id="product-1",
        product_name="T恤",
        unit_price=5000,
        quantity=2,
        subtotal=10000
    )
    db_session.add(order_item)
    await db_session.flush()

    approved_at = datetime.utcnow()
    completed_at = datetime.utcnow()

    return_request = OrderReturn(
        id="return-refund-1",
        order_id="order-ret-6",
        order_item_id="item-ret-6",
        return_reason="quality_issue",
        return_type="refund_only",
        status="completed",
        refund_amount=10000,
        refund_transaction_id="wx_refund_123456",
        approved_at=approved_at,
        completed_at=completed_at
    )
    db_session.add(return_request)
    await db_session.commit()
    await db_session.refresh(return_request)

    assert return_request.status == "completed"
    assert return_request.refund_amount == 10000
    assert return_request.refund_transaction_id == "wx_refund_123456"
    assert return_request.approved_at is not None
    assert return_request.completed_at is not None


@pytest.mark.asyncio
async def test_order_return_with_admin_notes(db_session):
    """Test order return with admin notes"""
    user = User(
        id="user-ret-7",
        openid="wx-test-ret-7",
        anonymous_name="测试用户11"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-ret-7",
        user_id="user-ret-7",
        order_number="ORD202502240011",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        id="item-ret-7",
        order_id="order-ret-7",
        product_id="product-1",
        product_name="T恤",
        unit_price=5000,
        quantity=2,
        subtotal=10000
    )
    db_session.add(order_item)
    await db_session.flush()

    return_request = OrderReturn(
        id="return-admin-1",
        order_id="order-ret-7",
        order_item_id="item-ret-7",
        return_reason="other",
        return_description="不想要了",
        return_type="refund_only",
        status="approved",
        admin_id="admin-1",
        admin_notes="用户反馈良好，同意退款"
    )
    db_session.add(return_request)
    await db_session.commit()
    await db_session.refresh(return_request)

    assert return_request.admin_id == "admin-1"
    assert return_request.admin_notes == "用户反馈良好，同意退款"
    assert return_request.status == "approved"


@pytest.mark.asyncio
async def test_order_shipment_order_relationship(db_session):
    """Test relationship between Order and OrderShipment"""
    user = User(
        id="user-rel-1",
        openid="wx-test-rel-1",
        anonymous_name="测试用户12"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-rel-1",
        user_id="user-rel-1",
        order_number="ORD202502240012",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    shipment = OrderShipment(
        id="shipment-rel-1",
        order_id="order-rel-1",
        courier_code="SF",
        courier_name="顺丰速运",
        tracking_number="SF9999999999",
        status="in_transit",
        shipped_at=datetime.utcnow()
    )
    db_session.add(shipment)
    await db_session.commit()

    # Verify shipment is linked to order
    result = await db_session.execute(
        select(OrderShipment).where(OrderShipment.order_id == "order-rel-1")
    )
    found_shipment = result.scalar_one()
    assert found_shipment is not None
    assert found_shipment.id == "shipment-rel-1"


@pytest.mark.asyncio
async def test_order_return_order_item_relationship(db_session):
    """Test relationship between OrderReturn and OrderItem"""
    user = User(
        id="user-rel-2",
        openid="wx-test-rel-2",
        anonymous_name="测试用户13"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-rel-2",
        user_id="user-rel-2",
        order_number="ORD202502240013",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        id="item-rel-1",
        order_id="order-rel-2",
        product_id="product-1",
        product_name="T恤",
        unit_price=5000,
        quantity=2,
        subtotal=10000
    )
    db_session.add(order_item)
    await db_session.flush()

    return_request = OrderReturn(
        id="return-rel-1",
        order_id="order-rel-2",
        order_item_id="item-rel-1",
        return_reason="quality_issue",
        return_type="refund_only",
        status="requested"
    )
    db_session.add(return_request)
    await db_session.commit()

    # Verify return is linked to order item
    result = await db_session.execute(
        select(OrderReturn).where(OrderReturn.order_item_id == "item-rel-1")
    )
    found_return = result.scalar_one()
    assert found_return is not None
    assert found_return.id == "return-rel-1"
