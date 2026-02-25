"""
单元测试 - 订单模式 (app.schemas.order)
"""
from datetime import datetime

import pytest
from pydantic import ValidationError


class TestOrderItemCreate:
    """测试订单明细创建模式"""

    def test_valid_order_item_create(self):
        """测试有效的订单明细创建"""
        from app.schemas.order import OrderItemCreate

        item = OrderItemCreate(
            sku_id="sku_123",
            quantity=2
        )
        assert item.sku_id == "sku_123"
        assert item.quantity == 2

    def test_quantity_must_be_positive(self):
        """测试数量必须大于等于1"""
        from app.schemas.order import OrderItemCreate

        with pytest.raises(ValidationError) as exc_info:
            OrderItemCreate(sku_id="sku_123", quantity=0)
        assert "quantity" in str(exc_info.value).lower()

    def test_quantity_cannot_be_negative(self):
        """测试数量不能为负数"""
        from app.schemas.order import OrderItemCreate

        with pytest.raises(ValidationError) as exc_info:
            OrderItemCreate(sku_id="sku_123", quantity=-1)
        assert "quantity" in str(exc_info.value).lower()


class TestOrderItemResponse:
    """测试订单明细响应模式"""

    def test_order_item_response_fields(self):
        """测试订单明细响应字段"""
        from app.schemas.order import OrderItemResponse

        item = OrderItemResponse(
            id="item_123",
            order_id="order_456",
            product_id="product_789",
            sku_id="sku_123",
            product_name="测试商品",
            sku_name="红色-L码",
            product_image="https://example.com/image.jpg",
            attributes={"color": "红色", "size": "L"},
            unit_price="99.99",
            quantity=2,
            subtotal="199.98",
            bundle_components=None
        )
        assert item.id == "item_123"
        assert item.product_name == "测试商品"
        assert item.attributes == {"color": "红色", "size": "L"}

    def test_json_serialization(self):
        """测试JSON序列化"""
        from app.schemas.order import OrderItemResponse

        item = OrderItemResponse(
            id="item_123",
            order_id="order_456",
            product_id="product_789",
            sku_id="sku_123",
            product_name="测试商品",
            sku_name="红色-L码",
            product_image="https://example.com/image.jpg",
            attributes={"color": "红色", "size": "L"},
            unit_price="99.99",
            quantity=2,
            subtotal="199.98",
            bundle_components=None
        )
        json_data = item.model_dump_json()
        assert "item_123" in json_data
        assert "测试商品" in json_data

    def test_bundle_components_serialization(self):
        """测试套餐组件JSON序列化"""
        from app.schemas.order import OrderItemResponse

        bundle_data = [
            {"product_id": "p1", "sku_id": "s1", "quantity": 1},
            {"product_id": "p2", "sku_id": "s2", "quantity": 2}
        ]

        item = OrderItemResponse(
            id="item_123",
            order_id="order_456",
            product_id="product_789",
            sku_id="sku_123",
            product_name="测试套餐",
            sku_name="标准套餐",
            product_image="https://example.com/bundle.jpg",
            attributes={"type": "bundle"},
            unit_price="199.99",
            quantity=1,
            subtotal="199.99",
            bundle_components=bundle_data
        )
        assert item.bundle_components == bundle_data


class TestOrderCreate:
    """测试订单创建模式"""

    def test_valid_order_create(self):
        """测试有效的订单创建"""
        from app.schemas.order import OrderCreate

        order = OrderCreate(
            items=[
                {"sku_id": "sku_1", "quantity": 2},
                {"sku_id": "sku_2", "quantity": 1}
            ],
            shipping_address_id="address_123",
            payment_method="wechat"
        )
        assert len(order.items) == 2
        assert order.shipping_address_id == "address_123"
        assert order.payment_method == "wechat"
        assert order.points_to_use == 0  # default value

    def test_payment_method_validation(self):
        """测试支付方式验证"""
        from app.schemas.order import OrderCreate

        # Valid payment methods
        valid_methods = ["wechat", "alipay", "points", "hybrid"]
        for method in valid_methods:
            order = OrderCreate(
                items=[{"sku_id": "sku_1", "quantity": 1}],
                shipping_address_id="address_123",
                payment_method=method
            )
            assert order.payment_method == method

    def test_invalid_payment_method(self):
        """测试无效的支付方式"""
        from app.schemas.order import OrderCreate

        with pytest.raises(ValidationError):
            OrderCreate(
                items=[{"sku_id": "sku_1", "quantity": 1}],
                shipping_address_id="address_123",
                payment_method="invalid_method"
            )

    def test_points_to_use_default(self):
        """测试积分使用默认值"""
        from app.schemas.order import OrderCreate

        order = OrderCreate(
            items=[{"sku_id": "sku_1", "quantity": 1}],
            shipping_address_id="address_123",
            payment_method="points"
        )
        assert order.points_to_use == 0

    def test_points_to_use_custom(self):
        """测试自定义积分使用"""
        from app.schemas.order import OrderCreate

        order = OrderCreate(
            items=[{"sku_id": "sku_1", "quantity": 1}],
            shipping_address_id="address_123",
            payment_method="hybrid",
            points_to_use=100
        )
        assert order.points_to_use == 100

    def test_items_cannot_be_empty(self):
        """测试订单明细不能为空"""
        from app.schemas.order import OrderCreate

        with pytest.raises(ValidationError):
            OrderCreate(
                items=[],
                shipping_address_id="address_123",
                payment_method="wechat"
            )


class TestOrderResponse:
    """测试订单响应模式"""

    def test_order_response_fields(self):
        """测试订单响应字段"""
        from app.schemas.order import OrderResponse

        order = OrderResponse(
            id="order_123",
            user_id="user_456",
            order_number="ORD20240224123456",
            total_amount="299.99",
            points_used=100,
            discount_amount="10.00",
            shipping_cost="5.00",
            final_amount="194.99",
            payment_method="hybrid",
            payment_status="pending",
            transaction_id=None,
            paid_at=None,
            status="pending",
            shipping_address_id="address_123",
            shipping_template_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            items=[],
            shipping_address=None
        )
        assert order.id == "order_123"
        assert order.order_number == "ORD20240224123456"
        assert order.payment_method == "hybrid"
        assert order.status == "pending"

    def test_order_with_items(self):
        """测试带订单明细的订单响应"""
        from app.schemas.order import OrderItemResponse, OrderResponse

        items = [
            OrderItemResponse(
                id="item_1",
                order_id="order_123",
                product_id="product_1",
                sku_id="sku_1",
                product_name="商品1",
                sku_name="SKU1",
                product_image="image1.jpg",
                attributes={"color": "red"},
                unit_price="99.99",
                quantity=2,
                subtotal="199.98",
                bundle_components=None
            )
        ]

        order = OrderResponse(
            id="order_123",
            user_id="user_456",
            order_number="ORD20240224123456",
            total_amount="199.98",
            points_used=0,
            discount_amount="0.00",
            shipping_cost="0.00",
            final_amount="199.98",
            payment_method="wechat",
            payment_status="paid",
            transaction_id="wx_txn_123",
            paid_at=datetime.now(),
            status="paid",
            shipping_address_id="address_123",
            shipping_template_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            items=items,
            shipping_address=None
        )
        assert len(order.items) == 1
        assert order.items[0].product_name == "商品1"


class TestOrderUpdate:
    """测试订单更新模式"""

    def test_update_status(self):
        """测试更新订单状态"""
        from app.schemas.order import OrderUpdate

        update = OrderUpdate(status="paid")
        assert update.status == "paid"

    def test_update_shipping_address(self):
        """测试更新收货地址"""
        from app.schemas.order import OrderUpdate

        update = OrderUpdate(shipping_address_id="new_address_123")
        assert update.shipping_address_id == "new_address_123"

    def test_update_both_fields(self):
        """测试同时更新多个字段"""
        from app.schemas.order import OrderUpdate

        update = OrderUpdate(
            status="shipped",
            shipping_address_id="new_address_123"
        )
        assert update.status == "shipped"
        assert update.shipping_address_id == "new_address_123"

    def test_all_status_values(self):
        """测试所有订单状态值"""
        from app.schemas.order import OrderUpdate

        valid_statuses = [
            "pending", "paid", "processing", "shipped",
            "delivered", "completed", "cancelled", "refunding", "refunded"
        ]

        for status in valid_statuses:
            update = OrderUpdate(status=status)
            assert update.status == status

    def test_invalid_status(self):
        """测试无效的订单状态"""
        from app.schemas.order import OrderUpdate

        with pytest.raises(ValidationError):
            OrderUpdate(status="invalid_status")

    def test_optional_fields(self):
        """测试可选字段"""
        from app.schemas.order import OrderUpdate

        # Both fields optional
        update = OrderUpdate()
        assert update.status is None
        assert update.shipping_address_id is None
