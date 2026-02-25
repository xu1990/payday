"""
Order Service 测试 - 订单服务

测试覆盖：
1. create_order - 创建订单（成功、库存不足、SKU不存在、收货地址不存在）
2. get_order - 获取订单（成功、订单不存在、无权访问）
3. update_order_status - 更新订单状态（成功、状态无效、订单不存在）
4. cancel_order - 取消订单（成功、订单不存在、无权取消、已支付订单）
5. process_payment_callback - 处理支付回调（成功、订单不存在、重复支付）
6. 订单号生成（唯一性、格式）
7. 金额计算（商品总额、积分抵扣、运费、最终金额）
8. 库存锁定集成
9. 数据库事务回滚
10. 错误处理
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.exceptions import BusinessException, NotFoundException
from app.models.address import UserAddress
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductPrice, ProductSKU
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemCreate, OrderResponse
from app.services.order_service import OrderService
from sqlalchemy.exc import IntegrityError


def create_mock_redis():
    """创建mock Redis客户端"""
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.setex = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.hget = AsyncMock()
    mock_redis.hset = AsyncMock()
    mock_redis.hgetall = AsyncMock()
    mock_redis.hdel = AsyncMock()
    mock_redis.incr = AsyncMock()
    mock_redis.expire = AsyncMock()
    mock_redis.eval = AsyncMock()
    mock_redis.decrby = AsyncMock()
    mock_redis.pipeline = MagicMock()
    return mock_redis


def create_mock_db():
    """创建mock数据库session"""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    return mock_db


def create_mock_order():
    """创建mock订单对象"""
    order = MagicMock()
    order.id = "order_123"
    order.user_id = "user_123"
    order.order_number = "ORD20260224000001"
    order.total_amount = Decimal("10000")  # 100元
    order.points_used = 0
    order.discount_amount = Decimal("0")
    order.shipping_cost = Decimal("0")
    order.final_amount = Decimal("10000")
    order.payment_method = "wechat"
    order.payment_status = "pending"
    order.transaction_id = None
    order.paid_at = None
    order.status = "pending"
    order.shipping_address_id = "address_123"
    order.shipping_template_id = None
    order.created_at = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    order.items = []
    return order


def create_mock_sku(sku_id: str, product_id: str, stock: int = 100):
    """创建mock SKU对象"""
    sku = MagicMock()
    sku.id = sku_id
    sku.product_id = product_id
    sku.sku_code = f"SKU_{sku_id}"
    sku.name = "红色-L码"
    sku.attributes = {"color": "red", "size": "L"}  # Real dict, not MagicMock
    sku.stock = stock
    sku.is_active = True
    return sku


def create_mock_product(product_id: str, name: str = "测试商品"):
    """创建mock商品对象"""
    product = MagicMock()
    product.id = product_id
    product.name = name
    product.description = "商品描述"
    product.images = ["image.jpg"]  # Real list, not MagicMock
    product.product_type = "cash"
    product.item_type = "physical"
    product.is_active = True
    return product


def create_mock_price(sku_id: str, price: int = 10000, currency: str = "CNY"):
    """创建mock价格对象"""
    price_obj = MagicMock()
    price_obj.sku_id = sku_id
    price_obj.price_amount = price
    price_obj.currency = currency
    price_obj.price_type = "base"
    price_obj.is_active = True
    return price_obj


def create_mock_order_item(item_id: str = "item_123", sku_id: str = "sku_123", quantity: int = 2):
    """创建mock订单明细对象"""
    item = MagicMock()
    item.id = item_id
    item.order_id = "order_123"
    item.product_id = "product_123"
    item.sku_id = sku_id
    item.product_name = "测试商品"
    item.sku_name = "红色-L码"
    item.product_image = "image.jpg"
    item.attributes = {"color": "red"}
    item.unit_price = 10000
    item.quantity = quantity
    item.subtotal = 20000
    item.bundle_components = None
    return item


class TestGenerateOrderNumber:
    """测试订单号生成"""

    @pytest.mark.asyncio
    async def test_generate_order_number_format(self):
        """测试订单号格式正确"""
        with patch('app.services.order_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260224"

            mock_redis = create_mock_redis()
            mock_redis.incr = AsyncMock(return_value=1)

            service = OrderService(redis_client=mock_redis)
            order_number = await service.generate_order_number()

            assert order_number.startswith("ORD20260224")
            assert len(order_number) == 17  # ORD + 8 digits (YYYYMMDD) + 6 digits (sequence)

    @pytest.mark.asyncio
    async def test_generate_order_number_sequence(self):
        """测试订单号序列递增"""
        with patch('app.services.order_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260224"

            mock_redis = create_mock_redis()
            mock_redis.incr = AsyncMock(side_effect=[1, 2, 3])

            service = OrderService(redis_client=mock_redis)

            num1 = await service.generate_order_number()
            num2 = await service.generate_order_number()
            num3 = await service.generate_order_number()

            assert num1 == "ORD20260224000001"
            assert num2 == "ORD20260224000002"
            assert num3 == "ORD20260224000003"

    @pytest.mark.asyncio
    async def test_generate_order_number_padded(self):
        """测试订单号数字补零"""
        with patch('app.services.order_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260224"

            mock_redis = create_mock_redis()
            mock_redis.incr = AsyncMock(return_value=999)

            service = OrderService(redis_client=mock_redis)
            order_number = await service.generate_order_number()

            assert order_number == "ORD20260224000999"


class TestCreateOrder:
    """测试创建订单"""

    @pytest.mark.asyncio
    async def test_create_order_success_single_item(self):
        """测试创建订单成功（单个商品）"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            create_mock_product("product_123"),  # Product
            create_mock_sku("sku_123", "product_123", stock=100),  # SKU
            create_mock_price("sku_123", 10000),  # Price
            MagicMock(id="address_123", user_id="user_123"),  # Address
        ]
        mock_db.execute.return_value = mock_result

        # Mock stock lock
        mock_redis.eval = AsyncMock(return_value=1)  # Lock successful
        mock_redis.incr = AsyncMock(return_value=1)  # Order number sequence

        # Mock order creation
        mock_db.flush = AsyncMock()

        order_data = OrderCreate(
            items=[OrderItemCreate(sku_id="sku_123", quantity=2)],
            shipping_address_id="address_123",
            payment_method="wechat",
            points_to_use=0
        )

        service = OrderService(redis_client=mock_redis)
        order = await service.create_order(mock_db, "user_123", order_data)

        assert isinstance(order, OrderResponse)
        assert order.user_id == "user_123"
        assert len(order.items) == 1
        assert order.items[0].quantity == 2
        assert order.total_amount == "20000"  # 100 * 2
        assert order.status == "pending"

    @pytest.mark.asyncio
    async def test_create_order_success_multiple_items(self):
        """测试创建订单成功（多个商品）"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        # Mock database queries for multiple items
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            # First item
            create_mock_product("product_1"),
            create_mock_sku("sku_1", "product_1", stock=100),
            create_mock_price("sku_1", 10000),
            # Second item
            create_mock_product("product_2"),
            create_mock_sku("sku_2", "product_2", stock=50),
            create_mock_price("sku_2", 5000),
            # Address
            MagicMock(id="address_123", user_id="user_123"),
        ]
        mock_db.execute.return_value = mock_result

        # Mock stock locks
        mock_redis.eval = AsyncMock(return_value=1)
        mock_redis.incr = AsyncMock(return_value=1)
        mock_db.flush = AsyncMock()

        order_data = OrderCreate(
            items=[
                OrderItemCreate(sku_id="sku_1", quantity=2),
                OrderItemCreate(sku_id="sku_2", quantity=3),
            ],
            shipping_address_id="address_123",
            payment_method="wechat",
            points_to_use=0
        )

        service = OrderService(redis_client=mock_redis)
        order = await service.create_order(mock_db, "user_123", order_data)

        assert len(order.items) == 2
        assert order.total_amount == "35000"  # (100 * 2) + (50 * 3)
        assert order.item_count == 5

    @pytest.mark.asyncio
    async def test_create_order_with_points(self):
        """测试创建订单使用积分"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            create_mock_product("product_123"),
            create_mock_sku("sku_123", "product_123", stock=100),
            create_mock_price("sku_123", 10000),
            MagicMock(id="address_123", user_id="user_123"),
            MagicMock(id="user_123", points=5000),  # User points
        ]
        mock_db.execute.return_value = mock_result
        mock_redis.eval = AsyncMock(return_value=1)
        mock_redis.incr = AsyncMock(return_value=1)
        mock_db.flush = AsyncMock()

        order_data = OrderCreate(
            items=[OrderItemCreate(sku_id="sku_123", quantity=2)],
            shipping_address_id="address_123",
            payment_method="hybrid",
            points_to_use=1000
        )

        service = OrderService(redis_client=mock_redis)
        order = await service.create_order(mock_db, "user_123", order_data)

        assert order.points_used == 1000
        # Points discount: 1000 points = 10 yuan = 1000 fen
        # Final amount: 20000 - 1000 = 19000
        assert order.final_amount == "19000"

    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock(self):
        """测试创建订单库存不足"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            create_mock_product("product_123"),
            create_mock_sku("sku_123", "product_123", stock=5),  # Only 5 in stock
            create_mock_price("sku_123", 10000),
        ]
        mock_db.execute.return_value = mock_result

        # Stock lock fails
        mock_redis.eval = AsyncMock(return_value=0)  # Lock failed

        order_data = OrderCreate(
            items=[OrderItemCreate(sku_id="sku_123", quantity=10)],  # Request 10
            shipping_address_id="address_123",
            payment_method="wechat",
            points_to_use=0
        )

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(BusinessException) as exc_info:
            await service.create_order(mock_db, "user_123", order_data)

        assert "库存不足" in str(exc_info.value)
        assert exc_info.value.code == "INSUFFICIENT_STOCK"

    @pytest.mark.asyncio
    async def test_create_order_sku_not_found(self):
        """测试创建订单SKU不存在"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # SKU not found
        mock_db.execute.return_value = mock_result

        order_data = OrderCreate(
            items=[OrderItemCreate(sku_id="invalid_sku", quantity=1)],
            shipping_address_id="address_123",
            payment_method="wechat",
            points_to_use=0
        )

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(NotFoundException) as exc_info:
            await service.create_order(mock_db, "user_123", order_data)

        assert "SKU不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_order_address_not_found(self):
        """测试创建订单收货地址不存在"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            create_mock_product("product_123"),
            create_mock_sku("sku_123", "product_123", stock=100),
            create_mock_price("sku_123", 10000),
            None,  # Address not found
        ]
        mock_db.execute.return_value = mock_result
        mock_redis.eval = AsyncMock(return_value=1)

        order_data = OrderCreate(
            items=[OrderItemCreate(sku_id="sku_123", quantity=1)],
            shipping_address_id="invalid_address",
            payment_method="wechat",
            points_to_use=0
        )

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(NotFoundException) as exc_info:
            await service.create_order(mock_db, "user_123", order_data)

        assert "收货地址不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_order_insufficient_points(self):
        """测试创建订单积分不足"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            create_mock_product("product_123"),
            create_mock_sku("sku_123", "product_123", stock=100),
            create_mock_price("sku_123", 10000),
            MagicMock(id="address_123", user_id="user_123"),
            MagicMock(id="user_123", points=500),  # Only 500 points
        ]
        mock_db.execute.return_value = mock_result
        mock_redis.eval = AsyncMock(return_value=1)
        mock_db.flush = AsyncMock()

        order_data = OrderCreate(
            items=[OrderItemCreate(sku_id="sku_123", quantity=2)],
            shipping_address_id="address_123",
            payment_method="hybrid",
            points_to_use=1000  # Try to use 1000
        )

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(BusinessException) as exc_info:
            await service.create_order(mock_db, "user_123", order_data)

        assert "积分不足" in str(exc_info.value)
        assert exc_info.value.code == "INSUFFICIENT_POINTS"

    @pytest.mark.asyncio
    async def test_create_order_locks_stock(self):
        """测试创建订单锁定库存"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            create_mock_product("product_123"),
            create_mock_sku("sku_123", "product_123", stock=100),
            create_mock_price("sku_123", 10000),
            MagicMock(id="address_123", user_id="user_123"),
        ]
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()

        order_data = OrderCreate(
            items=[OrderItemCreate(sku_id="sku_123", quantity=5)],
            shipping_address_id="address_123",
            payment_method="wechat",
            points_to_use=0
        )

        service = OrderService(redis_client=mock_redis)
        await service.create_order(mock_db, "user_123", order_data)

        # Verify stock lock was called
        assert mock_redis.eval.call_count == 1
        call_args = mock_redis.eval.call_args
        assert call_args[0][1] == 2  # Number of keys
        assert "sku_123" in call_args[0][2]  # First key

    @pytest.mark.asyncio
    async def test_create_order_rollback_on_error(self):
        """测试创建订单失败时回滚并释放库存锁定"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            create_mock_product("product_123"),
            create_mock_sku("sku_123", "product_123", stock=100),
            create_mock_price("sku_123", 10000),
            MagicMock(id="address_123", user_id="user_123"),
        ]
        mock_db.execute.return_value = mock_result
        mock_redis.eval = AsyncMock(return_value=1)
        mock_redis.incr = AsyncMock(return_value=1)

        # Simulate database error
        mock_db.flush = AsyncMock(side_effect=IntegrityError("Constraint failed", {}, None))

        order_data = OrderCreate(
            items=[OrderItemCreate(sku_id="sku_123", quantity=1)],
            shipping_address_id="address_123",
            payment_method="wechat",
            points_to_use=0
        )

        service = OrderService(redis_client=mock_redis)

        # IntegrityError is re-raised after cleanup
        with pytest.raises(IntegrityError):
            await service.create_order(mock_db, "user_123", order_data)

        # Verify rollback was called
        mock_db.rollback.assert_called_once()

        # Verify stock lock was acquired (eval called once)
        assert mock_redis.eval.call_count == 1

        # Verify stock lock was released (decrby called to release)
        mock_redis.decrby.assert_called_once()
        # Check that it was called with the correct lock key and quantity
        call_args = mock_redis.decrby.call_args
        assert "sku_123" in call_args[0][0]  # lock key contains sku_id
        assert call_args[0][1] == 1  # quantity

    @pytest.mark.asyncio
    async def test_create_order_multi_item_stock_cleanup_on_failure(self):
        """测试多商品订单创建失败时释放所有已锁定的库存"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        # First two items have stock, third item fails
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            create_mock_product("product_1"),      # Item 1: product
            create_mock_sku("sku_1", "product_1", stock=100),  # Item 1: SKU
            create_mock_price("sku_1", 10000),     # Item 1: price
            create_mock_product("product_2"),      # Item 2: product
            create_mock_sku("sku_2", "product_2", stock=50),   # Item 2: SKU
            create_mock_price("sku_2", 20000),     # Item 2: price
            create_mock_product("product_3"),      # Item 3: product
            create_mock_sku("sku_3", "product_3", stock=0),    # Item 3: SKU - no stock!
            create_mock_price("sku_3", 30000),     # Item 3: price
        ]
        mock_db.execute.return_value = mock_result

        # Stock lock: first two succeed, third fails
        mock_redis.eval = AsyncMock(side_effect=[1, 1, 0])  # Lock, Lock, Fail
        mock_redis.incr = AsyncMock(return_value=1)

        order_data = OrderCreate(
            items=[
                OrderItemCreate(sku_id="sku_1", quantity=2),
                OrderItemCreate(sku_id="sku_2", quantity=3),
                OrderItemCreate(sku_id="sku_3", quantity=1),
            ],
            shipping_address_id="address_123",
            payment_method="wechat",
            points_to_use=0
        )

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(BusinessException) as exc_info:
            await service.create_order(mock_db, "user_123", order_data)

        assert "库存不足" in str(exc_info.value)
        assert exc_info.value.code == "INSUFFICIENT_STOCK"

        # Verify that eval was called 3 times for acquire (sku_1, sku_2, sku_3)
        assert mock_redis.eval.call_count == 3

        # Verify that decrby was called 2 times to release locks for sku_1 and sku_2
        assert mock_redis.decrby.call_count == 2

        # Verify the releases were for the correct SKUs and quantities
        decrby_calls = mock_redis.decrby.call_args_list
        released_skus = [call[0][0] for call in decrby_calls]
        released_quantities = [call[0][1] for call in decrby_calls]

        # Should have released sku_1 with quantity 2 and sku_2 with quantity 3
        assert any("sku_1" in sku for sku in released_skus)
        assert any("sku_2" in sku for sku in released_skus)
        assert 2 in released_quantities
        assert 3 in released_quantities

        # Verify rollback was called
        mock_db.rollback.assert_called_once()



class TestGetOrder:
    """测试获取订单"""

    @pytest.mark.asyncio
    async def test_get_order_success(self):
        """测试获取订单成功"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_order = create_mock_order()
        mock_order.items = [
            create_mock_order_item("item_1", "sku_123", 2)
        ]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        mock_db.execute.return_value = mock_result

        service = OrderService(redis_client=mock_redis)
        order = await service.get_order(mock_db, "order_123", "user_123")

        assert isinstance(order, OrderResponse)
        assert order.id == "order_123"
        assert order.user_id == "user_123"
        assert len(order.items) == 1

    @pytest.mark.asyncio
    async def test_get_order_not_found(self):
        """测试获取不存在的订单"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(NotFoundException) as exc_info:
            await service.get_order(mock_db, "invalid_order", "user_123")

        assert "订单不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_order_unauthorized(self):
        """测试获取其他用户的订单"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_order = create_mock_order()
        mock_order.user_id = "other_user"  # Different user

        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = mock_order
        mock_db.execute.return_value = mock_result

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(BusinessException) as exc_info:
            await service.get_order(mock_db, "order_123", "user_123")

        assert "无权访问" in str(exc_info.value)
        assert exc_info.value.code == "FORBIDDEN"


class TestUpdateOrderStatus:
    """测试更新订单状态"""

    @pytest.mark.asyncio
    async def test_update_status_success(self):
        """测试更新状态成功"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_order = create_mock_order()
        mock_order.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        service = OrderService(redis_client=mock_redis)
        order = await service.update_order_status(mock_db, "order_123", "paid")

        assert order.status == "paid"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_order_not_found(self):
        """测试更新不存在的订单状态"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(NotFoundException) as exc_info:
            await service.update_order_status(mock_db, "invalid_order", "paid")

        assert "订单不存在" in str(exc_info.value)


class TestCancelOrder:
    """测试取消订单"""

    @pytest.mark.asyncio
    async def test_cancel_order_success(self):
        """测试取消订单成功"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_order = create_mock_order()
        mock_order.status = "pending"
        mock_order.items = [
            create_mock_order_item("item_1", "sku_123", 2)
        ]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        service = OrderService(redis_client=mock_redis)
        order = await service.cancel_order(mock_db, "order_123", "user_123", "不想要了")

        assert order.status == "cancelled"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_order_releases_stock(self):
        """测试取消订单释放库存"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_order = create_mock_order()
        mock_order.status = "pending"
        mock_order.items = [
            create_mock_order_item("item_1", "sku_123", 5),
            create_mock_order_item("item_2", "sku_456", 3)
        ]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        service = OrderService(redis_client=mock_redis)
        await service.cancel_order(mock_db, "order_123", "user_123", "不想要了")

        # Verify stock release was called for each item
        assert mock_redis.decrby.call_count == 2

    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self):
        """测试取消不存在的订单"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(NotFoundException) as exc_info:
            await service.cancel_order(mock_db, "invalid_order", "user_123", "不想要了")

        assert "订单不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cancel_order_unauthorized(self):
        """测试取消其他用户的订单"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_order = create_mock_order()
        mock_order.user_id = "other_user"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        mock_db.execute.return_value = mock_result

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(BusinessException) as exc_info:
            await service.cancel_order(mock_db, "order_123", "user_123", "不想要了")

        assert "无权访问" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cancel_paid_order_forbidden(self):
        """测试取消已支付订单失败"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_order = create_mock_order()
        mock_order.status = "paid"
        mock_order.payment_status = "paid"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        mock_db.execute.return_value = mock_result

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(BusinessException) as exc_info:
            await service.cancel_order(mock_db, "order_123", "user_123", "不想要了")

        assert "已支付订单不能取消" in str(exc_info.value)
        assert exc_info.value.code == "INVALID_STATUS"


class TestProcessPaymentCallback:
    """测试处理支付回调"""

    @pytest.mark.asyncio
    async def test_payment_callback_success(self):
        """测试支付回调成功"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_order = create_mock_order()
        mock_order.status = "pending"
        mock_order.payment_status = "pending"
        mock_order.items = [
            MagicMock(sku_id="sku_123", quantity=2),
            MagicMock(sku_id="sku_456", quantity=3)
        ]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Mock pipeline for stock confirmation
        mock_pipeline = MagicMock()
        mock_pipeline.decrby = MagicMock()
        mock_pipeline.execute = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline

        service = OrderService(redis_client=mock_redis)
        order = await service.process_payment_callback(
            mock_db, "order_123", "txn_123456"
        )

        assert order.status == "paid"
        assert order.payment_status == "paid"
        assert order.transaction_id == "txn_123456"
        assert order.paid_at is not None

    @pytest.mark.asyncio
    async def test_payment_callback_confirms_stock(self):
        """测试支付回调确认库存"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_order = create_mock_order()
        mock_order.status = "pending"
        mock_order.payment_status = "pending"
        mock_order.items = [
            MagicMock(sku_id="sku_123", quantity=2),
            MagicMock(sku_id="sku_456", quantity=3)
        ]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.decrby = MagicMock()
        mock_pipeline.execute = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline

        service = OrderService(redis_client=mock_redis)
        await service.process_payment_callback(mock_db, "order_123", "txn_123456")

        # Verify stock confirmation (lock_key and stock_key for each item)
        assert mock_pipeline.decrby.call_count == 4  # 2 items * 2 keys each

    @pytest.mark.asyncio
    async def test_payment_callback_order_not_found(self):
        """测试支付回调订单不存在"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(NotFoundException) as exc_info:
            await service.process_payment_callback(mock_db, "invalid_order", "txn_123")

        assert "订单不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_payment_callback_duplicate_payment(self):
        """测试重复支付回调"""
        mock_db = create_mock_db()
        mock_redis = create_mock_redis()

        mock_order = create_mock_order()
        mock_order.status = "paid"
        mock_order.payment_status = "paid"
        mock_order.transaction_id = "txn_original"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        mock_db.execute.return_value = mock_result

        service = OrderService(redis_client=mock_redis)

        with pytest.raises(BusinessException) as exc_info:
            await service.process_payment_callback(mock_db, "order_123", "txn_new")

        assert "订单已支付" in str(exc_info.value)
        assert exc_info.value.code == "ALREADY_PAID"
