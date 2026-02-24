"""
Tests for Order and OrderItem models
"""
import pytest
from datetime import datetime
from sqlalchemy import select, func, text
from app.models.order import Order, OrderItem
from app.models.user import User
from app.models.address import UserAddress


@pytest.mark.asyncio
async def test_create_order_basic(db_session):
    """Test creating an order with basic fields"""
    # Create a user first
    user = User(
        id="user-1",
        openid="wx-test-openid",
        anonymous_name="测试用户"
    )
    db_session.add(user)
    await db_session.flush()

    # Create order
    order = Order(
        id="order-1",
        user_id="user-1",
        order_number="ORD202502240001",
        total_amount=10000,  # 100.00 yuan in fen
        points_used=0,
        discount_amount=0,
        shipping_cost=0,
        final_amount=10000,
        payment_method="wechat",
        payment_status="pending",
        status="pending"
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    assert order.id == "order-1"
    assert order.user_id == "user-1"
    assert order.order_number == "ORD202502240001"
    assert order.total_amount == 10000
    assert order.final_amount == 10000
    assert order.payment_method == "wechat"
    assert order.payment_status == "pending"
    assert order.status == "pending"
    assert order.points_used == 0
    assert order.discount_amount == 0
    assert order.shipping_cost == 0


@pytest.mark.asyncio
async def test_create_order_with_payment_details(db_session):
    """Test creating an order with payment information"""
    user = User(
        id="user-2",
        openid="wx-test-openid-2",
        anonymous_name="测试用户2"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-2",
        user_id="user-2",
        order_number="ORD202502240002",
        total_amount=15000,
        points_used=500,
        discount_amount=1000,
        shipping_cost=1000,
        final_amount=14500,
        payment_method="hybrid",
        payment_status="paid",
        transaction_id="wx_txn_123456",
        paid_at=datetime.utcnow(),
        status="paid"
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    assert order.payment_method == "hybrid"
    assert order.payment_status == "paid"
    assert order.transaction_id == "wx_txn_123456"
    assert order.paid_at is not None
    assert order.points_used == 500
    assert order.discount_amount == 1000
    assert order.shipping_cost == 1000
    assert order.final_amount == 14500


@pytest.mark.asyncio
async def test_order_payment_method_enum(db_session):
    """Test all payment method enum values"""
    user = User(
        id="user-3",
        openid="wx-test-openid-3",
        anonymous_name="测试用户3"
    )
    db_session.add(user)
    await db_session.flush()

    payment_methods = ["wechat", "alipay", "points", "hybrid"]
    for i, method in enumerate(payment_methods):
        order = Order(
            id=f"order-method-{i}",
            user_id="user-3",
            order_number=f"ORD2025022400{i}",
            total_amount=10000,
            final_amount=10000,
            payment_method=method
        )
        db_session.add(order)

    await db_session.commit()

    # Verify all payment methods were created
    result = await db_session.execute(
        select(Order.payment_method).where(Order.user_id == "user-3")
    )
    methods = [row[0] for row in result]
    assert set(methods) == set(payment_methods)


@pytest.mark.asyncio
async def test_order_payment_status_enum(db_session):
    """Test all payment status enum values"""
    user = User(
        id="user-4",
        openid="wx-test-openid-4",
        anonymous_name="测试用户4"
    )
    db_session.add(user)
    await db_session.flush()

    payment_statuses = ["pending", "paid", "failed", "refunded"]
    for i, status in enumerate(payment_statuses):
        order = Order(
            id=f"order-paystatus-{i}",
            user_id="user-4",
            order_number=f"ORD2025022401{i}",
            total_amount=10000,
            final_amount=10000,
            payment_method="wechat",
            payment_status=status
        )
        db_session.add(order)

    await db_session.commit()

    # Verify all payment statuses were created
    result = await db_session.execute(
        select(Order.payment_status).where(Order.user_id == "user-4")
    )
    statuses = [row[0] for row in result]
    assert set(statuses) == set(payment_statuses)


@pytest.mark.asyncio
async def test_order_status_enum(db_session):
    """Test all order status enum values"""
    user = User(
        id="user-5",
        openid="wx-test-openid-5",
        anonymous_name="测试用户5"
    )
    db_session.add(user)
    await db_session.flush()

    order_statuses = [
        "pending", "paid", "processing", "shipped",
        "delivered", "completed", "cancelled", "refunding", "refunded"
    ]
    for i, status in enumerate(order_statuses):
        order = Order(
            id=f"order-status-{i}",
            user_id="user-5",
            order_number=f"ORD2025022501{i}",
            total_amount=10000,
            final_amount=10000,
            payment_method="wechat",
            status=status
        )
        db_session.add(order)

    await db_session.commit()

    # Verify all statuses were created
    result = await db_session.execute(
        select(Order.status).where(Order.user_id == "user-5")
    )
    statuses = [row[0] for row in result]
    assert set(statuses) == set(order_statuses)


@pytest.mark.asyncio
async def test_create_order_with_shipping_address(db_session):
    """Test creating order with shipping address"""
    # Create user
    user = User(
        id="user-6",
        openid="wx-test-openid-6",
        anonymous_name="测试用户6"
    )
    db_session.add(user)
    await db_session.flush()

    # Create address
    from app.models.address import AdminRegion

    region = AdminRegion(
        id="region-1",
        code="110000",
        name="北京市",
        level="province"
    )
    db_session.add(region)
    await db_session.flush()

    address = UserAddress(
        id="addr-1",
        user_id="user-6",
        province_code="110000",
        province_name="北京市",
        city_code="110100",
        city_name="北京市",
        district_code="110101",
        district_name="东城区",
        detailed_address="某某街道123号",
        contact_name="张三",
        contact_phone="13800138000",
        is_default=True
    )
    db_session.add(address)
    await db_session.flush()

    # Create order with shipping address
    order = Order(
        id="order-6",
        user_id="user-6",
        order_number="ORD202502260001",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat",
        shipping_address_id="addr-1"
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Get order with address
    result = await db_session.execute(
        select(Order).where(Order.id == "order-6")
    )
    order = result.scalar_one()

    assert order.shipping_address_id == "addr-1"


@pytest.mark.asyncio
async def test_create_order_item_basic(db_session):
    """Test creating an order item with basic fields"""
    # Create order first
    user = User(
        id="user-7",
        openid="wx-test-openid-7",
        anonymous_name="测试用户7"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-7",
        user_id="user-7",
        order_number="ORD202502270001",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    # Create order item
    order_item = OrderItem(
        id="item-1",
        order_id="order-7",
        product_id="product-1",
        product_name="T恤",
        unit_price=5000,  # 50.00 yuan in fen
        quantity=2,
        subtotal=10000
    )
    db_session.add(order_item)
    await db_session.commit()
    await db_session.refresh(order_item)

    assert order_item.id == "item-1"
    assert order_item.order_id == "order-7"
    assert order_item.product_id == "product-1"
    assert order_item.product_name == "T恤"
    assert order_item.unit_price == 5000
    assert order_item.quantity == 2
    assert order_item.subtotal == 10000


@pytest.mark.asyncio
async def test_create_order_item_with_sku(db_session):
    """Test creating order item with SKU information"""
    user = User(
        id="user-8",
        openid="wx-test-openid-8",
        anonymous_name="测试用户8"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-8",
        user_id="user-8",
        order_number="ORD202502280001",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    # Create order item with SKU
    order_item = OrderItem(
        id="item-2",
        order_id="order-8",
        product_id="product-1",
        sku_id="sku-1",
        product_name="T恤",
        sku_name="红色 - L码",
        product_image="https://example.com/shirt.jpg",
        attributes={"color": "red", "size": "L"},
        unit_price=5000,
        quantity=2,
        subtotal=10000
    )
    db_session.add(order_item)
    await db_session.commit()
    await db_session.refresh(order_item)

    assert order_item.sku_id == "sku-1"
    assert order_item.sku_name == "红色 - L码"
    assert order_item.product_image == "https://example.com/shirt.jpg"
    assert order_item.attributes["color"] == "red"
    assert order_item.attributes["size"] == "L"


@pytest.mark.asyncio
async def test_order_item_json_attributes(db_session):
    """Test order item JSON attributes field"""
    user = User(
        id="user-9",
        openid="wx-test-openid-9",
        anonymous_name="测试用户9"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-9",
        user_id="user-9",
        order_number="ORD202502290001",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    # Test various attribute structures
    test_attributes = [
        {"color": "red", "size": "L", "material": "cotton"},
        {"flavor": "chocolate", "weight": "500g"},
        {"version": "pro", "storage": "256GB", "color": "black"}
    ]

    for i, attrs in enumerate(test_attributes):
        order_item = OrderItem(
            id=f"item-attr-{i}",
            order_id="order-9",
            product_id=f"product-{i}",
            product_name=f"Product {i}",
            attributes=attrs,
            unit_price=10000,
            quantity=1,
            subtotal=10000
        )
        db_session.add(order_item)

    await db_session.commit()

    # Verify attributes were stored correctly
    result = await db_session.execute(
        select(OrderItem.attributes).where(OrderItem.order_id == "order-9")
    )
    stored_attributes = [row[0] for row in result]
    for i, attrs in enumerate(stored_attributes):
        assert attrs == test_attributes[i]


@pytest.mark.asyncio
async def test_order_item_bundle_components(db_session):
    """Test order item bundle components JSON field"""
    user = User(
        id="user-10",
        openid="wx-test-openid-10",
        anonymous_name="测试用户10"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-10",
        user_id="user-10",
        order_number="ORD202503010001",
        total_amount=30000,
        final_amount=30000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    # Create bundle order item
    bundle_components = [
        {
            "product_id": "comp-1",
            "product_name": "手机壳",
            "sku_id": "comp-sku-1",
            "quantity": 1
        },
        {
            "product_id": "comp-2",
            "product_name": "贴膜",
            "sku_id": "comp-sku-2",
            "quantity": 2
        }
    ]

    order_item = OrderItem(
        id="item-bundle-1",
        order_id="order-10",
        product_id="bundle-1",
        product_name="数码套装",
        bundle_components=bundle_components,
        unit_price=30000,
        quantity=1,
        subtotal=30000
    )
    db_session.add(order_item)
    await db_session.commit()
    await db_session.refresh(order_item)

    assert order_item.bundle_components is not None
    assert len(order_item.bundle_components) == 2
    assert order_item.bundle_components[0]["product_name"] == "手机壳"
    assert order_item.bundle_components[1]["quantity"] == 2


@pytest.mark.asyncio
async def test_order_order_item_relationship(db_session):
    """Test relationship between Order and OrderItem"""
    user = User(
        id="user-11",
        openid="wx-test-openid-11",
        anonymous_name="测试用户11"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-11",
        user_id="user-11",
        order_number="ORD202503020001",
        total_amount=25000,
        final_amount=25000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.flush()

    # Create multiple order items
    items = [
        OrderItem(
            id=f"item-multi-{i}",
            order_id="order-11",
            product_id=f"product-{i}",
            product_name=f"Product {i}",
            unit_price=5000 * (i + 1),
            quantity=1,
            subtotal=5000 * (i + 1)
        )
        for i in range(3)
    ]

    for item in items:
        db_session.add(item)

    await db_session.commit()

    # Verify items are linked to order
    result = await db_session.execute(
        select(func.count()).select_from(OrderItem).where(OrderItem.order_id == "order-11")
    )
    count = result.scalar()
    assert count == 3


@pytest.mark.asyncio
async def test_order_timestamps(db_session):
    """Test order created_at and updated_at timestamps"""
    user = User(
        id="user-12",
        openid="wx-test-openid-12",
        anonymous_name="测试用户12"
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        id="order-12",
        user_id="user-12",
        order_number="ORD202503030001",
        total_amount=10000,
        final_amount=10000,
        payment_method="wechat"
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    assert order.created_at is not None
    assert order.updated_at is not None

    # Update the order
    order.status = "paid"
    await db_session.commit()
    await db_session.refresh(order)

    # updated_at should be different after update
    # (Note: this depends on database support for ON UPDATE CURRENT_TIMESTAMP)
