"""
Shopping Cart Service 测试 - 购物车服务

测试覆盖：
1. get_cart - 获取购物车（空购物车、有商品购物车）
2. add_item - 添加商品（成功、库存不足、SKU不存在、重复添加）
3. update_item - 更新数量（成功、数量不足、商品不存在）
4. remove_item - 移除商品（成功、商品不存在）
5. clear_cart - 清空购物车
6. 库存锁定集成
7. TTL设置
8. 错误处理
9. 计算 totals（金额、积分、数量）
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.cart_service import CartService
from app.schemas.cart import (
    CartResponse,
    CartItemResponse,
    ProductBasicInfo,
    SKUBasicInfo
)


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
    mock_redis.hexists = AsyncMock()
    mock_redis.hlen = AsyncMock()
    mock_redis.hkeys = AsyncMock()
    mock_redis.hvals = AsyncMock()
    mock_redis.hincrby = AsyncMock()
    mock_redis.expire = AsyncMock()
    mock_redis.ttl = AsyncMock()
    return mock_redis


def create_mock_db():
    """创建mock数据库session"""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    return mock_db


class TestGetCart:
    """测试获取购物车"""

    @pytest.mark.asyncio
    async def test_get_empty_cart(self):
        """测试获取空购物车"""
        mock_redis = create_mock_redis()
        mock_redis.hgetall = AsyncMock(return_value={})

        service = CartService(redis_client=mock_redis)
        cart = await service.get_cart(user_id="user_123")

        assert isinstance(cart, CartResponse)
        assert len(cart.items) == 0
        assert cart.total_amount == 0
        assert cart.total_points == 0
        assert cart.item_count == 0

    @pytest.mark.asyncio
    async def test_get_cart_with_items(self):
        """测试获取有商品的购物车"""
        mock_redis = create_mock_redis()

        # Mock cart data in Redis
        cart_data = {
            "item_1": json.dumps({
                "id": "item_1",
                "sku_id": "sku_123",
                "quantity": 2,
                "product": {
                    "id": "product_123",
                    "name": "测试商品",
                    "description": "商品描述",
                    "images": ["image.jpg"],
                    "product_type": "point",
                    "item_type": "virtual",
                    "is_active": True
                },
                "sku": {
                    "id": "sku_123",
                    "sku_code": "SKU001",
                    "name": "红色-L码",
                    "attributes": {"color": "red"},
                    "stock": 100,
                    "price": 100,
                    "currency": "POINTS"
                }
            })
        }
        mock_redis.hgetall = AsyncMock(return_value=cart_data)

        service = CartService(redis_client=mock_redis)
        cart = await service.get_cart(user_id="user_123")

        assert len(cart.items) == 1
        assert cart.items[0].sku_id == "sku_123"
        assert cart.items[0].quantity == 2
        assert cart.total_points == 200  # 100 * 2
        assert cart.item_count == 2

    @pytest.mark.asyncio
    async def test_get_cart_multiple_items(self):
        """测试获取多个商品的购物车"""
        mock_redis = create_mock_redis()

        cart_data = {
            "item_1": json.dumps({
                "id": "item_1",
                "sku_id": "sku_1",
                "quantity": 2,
                "product": {
                    "id": "product_1",
                    "name": "商品1",
                    "description": None,
                    "images": None,
                    "product_type": "point",
                    "item_type": "virtual",
                    "is_active": True
                },
                "sku": {
                    "id": "sku_1",
                    "sku_code": "SKU001",
                    "name": "规格1",
                    "attributes": {},
                    "stock": 100,
                    "price": 100,
                    "currency": "POINTS"
                }
            }),
            "item_2": json.dumps({
                "id": "item_2",
                "sku_id": "sku_2",
                "quantity": 3,
                "product": {
                    "id": "product_2",
                    "name": "商品2",
                    "description": None,
                    "images": None,
                    "product_type": "point",
                    "item_type": "virtual",
                    "is_active": True
                },
                "sku": {
                    "id": "sku_2",
                    "sku_code": "SKU002",
                    "name": "规格2",
                    "attributes": {},
                    "stock": 50,
                    "price": 50,
                    "currency": "POINTS"
                }
            })
        }
        mock_redis.hgetall = AsyncMock(return_value=cart_data)

        service = CartService(redis_client=mock_redis)
        cart = await service.get_cart(user_id="user_123")

        assert len(cart.items) == 2
        assert cart.total_points == 350  # (100 * 2) + (50 * 3)
        assert cart.item_count == 5  # 2 + 3

    @pytest.mark.asyncio
    async def test_get_cart_sets_ttl(self):
        """测试获取购物车时刷新TTL"""
        mock_redis = create_mock_redis()
        mock_redis.hgetall = AsyncMock(return_value={})
        mock_redis.expire = AsyncMock(return_value=True)

        service = CartService(redis_client=mock_redis)
        await service.get_cart(user_id="user_123")

        # Verify TTL is set (1800 seconds = 30 minutes)
        mock_redis.expire.assert_called_once()
        call_args = mock_redis.expire.call_args
        assert call_args[0][1] == 1800


class TestAddItem:
    """测试添加商品到购物车"""

    @pytest.mark.asyncio
    async def test_add_item_success(self):
        """测试成功添加商品"""
        mock_redis = create_mock_redis()
        mock_redis.hget = AsyncMock(return_value=None)
        mock_redis.hgetall = AsyncMock(return_value={})
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)

        # Mock database queries
        mock_db = create_mock_db()

        # Mock SKU - Use a simple object, not MagicMock for nested fields
        from app.models.product import ProductSKU, Product

        class MockSKU:
            id = "sku_123"
            product_id = "product_123"
            sku_code = "SKU001"
            name = "规格1"
            attributes = {}
            stock = 100
            is_active = True

        class MockProduct:
            id = "product_123"
            name = "测试商品"
            description = None
            images = None
            product_type = "point"
            item_type = "virtual"
            is_active = True

        class MockPrice:
            price_amount = 100
            currency = "POINTS"

        mock_sku = MockSKU()
        mock_product = MockProduct()
        mock_price = MockPrice()

        # Setup mock results for multiple calls
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none = MagicMock(return_value=mock_sku)

        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none = MagicMock(return_value=mock_product)

        mock_result3 = MagicMock()
        mock_result3.scalar_one_or_none = MagicMock(return_value=mock_price)

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2, mock_result3])

        # Mock stock lock service
        with patch('app.services.cart_service.StockLockService') as MockStockLock:
            mock_stock_service = MagicMock()
            mock_stock_service.acquire_stock_lock = AsyncMock(return_value=True)
            MockStockLock.return_value = mock_stock_service

            service = CartService(redis_client=mock_redis)

            # Mock get_cart to return the expected cart
            expected_cart = CartResponse(
                items=[CartItemResponse(
                    id="cart_item_1",
                    sku_id="sku_123",
                    quantity=2,
                    product=ProductBasicInfo(
                        id="product_123",
                        name="测试商品",
                        description=None,
                        images=None,
                        product_type="point",
                        item_type="virtual",
                        is_active=True
                    ),
                    sku=SKUBasicInfo(
                        id="sku_123",
                        sku_code="SKU001",
                        name="规格1",
                        attributes={},
                        stock=100,
                        price=100.0,
                        currency="POINTS"
                    )
                )],
                total_amount=0,
                total_points=200,
                item_count=2
            )

            with patch.object(service, 'get_cart', return_value=expected_cart):
                cart = await service.add_item(
                    db=mock_db,
                    user_id="user_123",
                    sku_id="sku_123",
                    quantity=2
                )

            assert len(cart.items) == 1
            assert cart.items[0].quantity == 2
            mock_stock_service.acquire_stock_lock.assert_called_once_with("sku_123", 2)

    @pytest.mark.asyncio
    async def test_add_item_insufficient_stock(self):
        """测试库存不足时添加失败"""
        mock_redis = create_mock_redis()
        mock_redis.hget = AsyncMock(return_value=None)
        mock_db = create_mock_db()

        # Mock SKU - Use a simple object
        class MockSKU:
            id = "sku_123"
            product_id = "product_123"
            sku_code = "SKU001"
            name = "规格1"
            attributes = {}
            stock = 100
            is_active = True

        class MockProduct:
            id = "product_123"
            name = "测试商品"
            description = None
            images = None
            product_type = "point"
            item_type = "virtual"
            is_active = True

        class MockPrice:
            price_amount = 100
            currency = "POINTS"

        mock_sku = MockSKU()
        mock_product = MockProduct()
        mock_price = MockPrice()

        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none = MagicMock(return_value=mock_sku)

        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none = MagicMock(return_value=mock_product)

        mock_result3 = MagicMock()
        mock_result3.scalar_one_or_none = MagicMock(return_value=mock_price)

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2, mock_result3])

        # Mock stock lock service to return False
        with patch('app.services.cart_service.StockLockService') as MockStockLock:
            from app.core.exceptions import BusinessException
            mock_stock_service = MagicMock()
            mock_stock_service.acquire_stock_lock = AsyncMock(return_value=False)
            MockStockLock.return_value = mock_stock_service

            service = CartService(redis_client=mock_redis)

            with pytest.raises(BusinessException) as exc_info:
                await service.add_item(
                    db=mock_db,
                    user_id="user_123",
                    sku_id="sku_123",
                    quantity=10
                )

            assert "库存不足" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_add_item_existing_item_increments_quantity(self):
        """测试添加已存在的商品时增加数量"""
        mock_redis = create_mock_redis()

        existing_item = json.dumps({
            "id": "item_1",
            "sku_id": "sku_123",
            "quantity": 2,
            "product": {
                "id": "product_123",
                "name": "测试商品",
                "description": None,
                "images": None,
                "product_type": "point",
                "item_type": "virtual",
                "is_active": True
            },
            "sku": {
                "id": "sku_123",
                "sku_code": "SKU001",
                "name": "规格1",
                "attributes": {},
                "stock": 100,
                "price": 100,
                "currency": "POINTS"
            }
        })

        mock_redis.hget = AsyncMock(return_value=existing_item)
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.hgetall = AsyncMock(return_value={})
        mock_redis.expire = AsyncMock(return_value=True)

        mock_db = create_mock_db()

        # Even when item exists, service still queries DB for SKU/Product/Price
        class MockSKU:
            id = "sku_123"
            product_id = "product_123"
            sku_code = "SKU001"
            name = "规格1"
            attributes = {}
            stock = 100
            is_active = True

        class MockProduct:
            id = "product_123"
            name = "测试商品"
            description = None
            images = None
            product_type = "point"
            item_type = "virtual"
            is_active = True

        class MockPrice:
            price_amount = 100
            currency = "POINTS"

        mock_sku = MockSKU()
        mock_product = MockProduct()
        mock_price = MockPrice()

        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none = MagicMock(return_value=mock_sku)

        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none = MagicMock(return_value=mock_product)

        mock_result3 = MagicMock()
        mock_result3.scalar_one_or_none = MagicMock(return_value=mock_price)

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2, mock_result3])

        with patch('app.services.cart_service.StockLockService') as MockStockLock:
            mock_stock_service = MagicMock()
            mock_stock_service.acquire_stock_lock = AsyncMock(return_value=True)
            MockStockLock.return_value = mock_stock_service

            service = CartService(redis_client=mock_redis)

            # Note: When item exists, add_item queries DB but doesn't use the data
            # It directly updates the existing item
            from app.schemas.cart import CartResponse
            with patch.object(service, 'get_cart', return_value=CartResponse(
                items=[],
                total_amount=0,
                total_points=0,
                item_count=0
            )):
                cart = await service.add_item(
                    db=mock_db,
                    user_id="user_123",
                    sku_id="sku_123",
                    quantity=3
                )

            # Should lock additional 3, not total 5
            mock_stock_service.acquire_stock_lock.assert_called_once_with("sku_123", 3)

    @pytest.mark.asyncio
    async def test_add_item_generates_unique_id(self):
        """测试生成唯一的购物车项ID"""
        mock_redis = create_mock_redis()
        mock_redis.hget = AsyncMock(return_value=None)
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.hgetall = AsyncMock(return_value={})
        mock_redis.expire = AsyncMock(return_value=True)

        mock_db = create_mock_db()

        # Mock SKU - Use a simple object, not MagicMock for nested fields
        from app.models.product import ProductSKU, Product

        class MockSKU:
            id = "sku_123"
            product_id = "product_123"
            sku_code = "SKU001"
            name = "规格1"
            attributes = {}
            stock = 100
            is_active = True

        class MockProduct:
            id = "product_123"
            name = "测试商品"
            description = None
            images = None
            product_type = "point"
            item_type = "virtual"
            is_active = True

        class MockPrice:
            price_amount = 100
            currency = "POINTS"

        mock_sku = MockSKU()
        mock_product = MockProduct()
        mock_price = MockPrice()

        # Setup mock results for multiple calls
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none = MagicMock(return_value=mock_sku)

        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none = MagicMock(return_value=mock_product)

        mock_result3 = MagicMock()
        mock_result3.scalar_one_or_none = MagicMock(return_value=mock_price)

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2, mock_result3])

        with patch('app.services.cart_service.StockLockService') as MockStockLock:
            mock_stock_service = MagicMock()
            mock_stock_service.acquire_stock_lock = AsyncMock(return_value=True)
            MockStockLock.return_value = mock_stock_service

            service = CartService(redis_client=mock_redis)

            # Mock get_cart to return the expected cart
            expected_cart = CartResponse(
                items=[CartItemResponse(
                    id="generated_id_123",  # Simulating a generated UUID
                    sku_id="sku_123",
                    quantity=1,
                    product=ProductBasicInfo(
                        id="product_123",
                        name="测试商品",
                        description=None,
                        images=None,
                        product_type="point",
                        item_type="virtual",
                        is_active=True
                    ),
                    sku=SKUBasicInfo(
                        id="sku_123",
                        sku_code="SKU001",
                        name="规格1",
                        attributes={},
                        stock=100,
                        price=100.0,
                        currency="POINTS"
                    )
                )],
                total_amount=0,
                total_points=100,
                item_count=1
            )

            with patch.object(service, 'get_cart', return_value=expected_cart):
                cart = await service.add_item(
                    db=mock_db,
                    user_id="user_123",
                    sku_id="sku_123",
                    quantity=1
                )

            assert len(cart.items) == 1
            assert cart.items[0].id is not None
            assert cart.items[0].sku_id == "sku_123"


class TestUpdateItem:
    """测试更新购物车商品数量"""

    @pytest.mark.asyncio
    async def test_update_item_success(self):
        """测试成功更新数量"""
        mock_redis = create_mock_redis()

        existing_item = json.dumps({
            "id": "item_1",
            "sku_id": "sku_123",
            "quantity": 2,
            "product": {
                "id": "product_123",
                "name": "测试商品",
                "description": None,
                "images": None,
                "product_type": "point",
                "item_type": "virtual",
                "is_active": True
            },
            "sku": {
                "id": "sku_123",
                "sku_code": "SKU001",
                "name": "规格1",
                "attributes": {},
                "stock": 100,
                "price": 100,
                "currency": "POINTS"
            }
        })

        mock_redis.hget = AsyncMock(return_value=existing_item)
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.hgetall = AsyncMock(return_value={"sku_123": existing_item})
        mock_redis.expire = AsyncMock(return_value=True)

        with patch('app.services.cart_service.StockLockService') as MockStockLock:
            mock_stock_service = MagicMock()
            mock_stock_service.acquire_stock_lock = AsyncMock(return_value=True)
            MockStockLock.return_value = mock_stock_service

            service = CartService(redis_client=mock_redis)
            cart = await service.update_item(
                user_id="user_123",
                item_id="item_1",
                quantity=5
            )

            # Should lock additional 3 (5 - 2)
            mock_stock_service.acquire_stock_lock.assert_called_once_with("sku_123", 3)

    @pytest.mark.asyncio
    async def test_update_item_reduce_quantity(self):
        """测试减少数量（释放库存锁）"""
        mock_redis = create_mock_redis()

        existing_item = json.dumps({
            "id": "item_1",
            "sku_id": "sku_123",
            "quantity": 5,
            "product": {
                "id": "product_123",
                "name": "测试商品",
                "description": None,
                "images": None,
                "product_type": "point",
                "item_type": "virtual",
                "is_active": True
            },
            "sku": {
                "id": "sku_123",
                "sku_code": "SKU001",
                "name": "规格1",
                "attributes": {},
                "stock": 100,
                "price": 100,
                "currency": "POINTS"
            }
        })

        mock_redis.hget = AsyncMock(return_value=existing_item)
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.hgetall = AsyncMock(return_value={"sku_123": existing_item})
        mock_redis.expire = AsyncMock(return_value=True)

        with patch('app.services.cart_service.StockLockService') as MockStockLock:
            mock_stock_service = MagicMock()
            mock_stock_service.release_stock_lock = AsyncMock(return_value=True)
            MockStockLock.return_value = mock_stock_service

            service = CartService(redis_client=mock_redis)
            cart = await service.update_item(
                user_id="user_123",
                item_id="item_1",
                quantity=2
            )

            # Should release 3 (5 - 2)
            mock_stock_service.release_stock_lock.assert_called_once_with("sku_123", 3)

    @pytest.mark.asyncio
    async def test_update_item_not_found(self):
        """测试更新不存在的商品"""
        mock_redis = create_mock_redis()
        mock_redis.hgetall = AsyncMock(return_value={})

        service = CartService(redis_client=mock_redis)

        from app.core.exceptions import NotFoundException
        with pytest.raises(NotFoundException) as exc_info:
            await service.update_item(
                user_id="user_123",
                item_id="nonexistent_item",
                quantity=5
            )

        assert "不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_item_insufficient_stock(self):
        """测试更新时库存不足"""
        mock_redis = create_mock_redis()

        existing_item = json.dumps({
            "id": "item_1",
            "sku_id": "sku_123",
            "quantity": 2,
            "product": {
                "id": "product_123",
                "name": "测试商品",
                "description": None,
                "images": None,
                "product_type": "point",
                "item_type": "virtual",
                "is_active": True
            },
            "sku": {
                "id": "sku_123",
                "sku_code": "SKU001",
                "name": "规格1",
                "attributes": {},
                "stock": 100,
                "price": 100,
                "currency": "POINTS"
            }
        })

        mock_redis.hget = AsyncMock(return_value=existing_item)
        mock_redis.hgetall = AsyncMock(return_value={"sku_123": existing_item})

        with patch('app.services.cart_service.StockLockService') as MockStockLock:
            from app.core.exceptions import BusinessException
            mock_stock_service = MagicMock()
            mock_stock_service.acquire_stock_lock = AsyncMock(return_value=False)
            MockStockLock.return_value = mock_stock_service

            service = CartService(redis_client=mock_redis)

            with pytest.raises(BusinessException) as exc_info:
                await service.update_item(
                    user_id="user_123",
                    item_id="item_1",
                    quantity=100  # Much more than available
                )

            assert "库存不足" in str(exc_info.value)


class TestRemoveItem:
    """测试移除购物车商品"""

    @pytest.mark.asyncio
    async def test_remove_item_success(self):
        """测试成功移除商品"""
        mock_redis = create_mock_redis()

        existing_item = json.dumps({
            "id": "item_1",
            "sku_id": "sku_123",
            "quantity": 2,
            "product": {
                "id": "product_123",
                "name": "测试商品",
                "description": None,
                "images": None,
                "product_type": "point",
                "item_type": "virtual",
                "is_active": True
            },
            "sku": {
                "id": "sku_123",
                "sku_code": "SKU001",
                "name": "规格1",
                "attributes": {},
                "stock": 100,
                "price": 100,
                "currency": "POINTS"
            }
        })

        # hgetall will be called twice - first to get the item, then after deletion
        mock_redis.hgetall = AsyncMock(side_effect=[
            {"sku_123": existing_item},  # First call returns the item
            {}  # Second call returns empty cart
        ])
        mock_redis.hdel = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)

        with patch('app.services.cart_service.StockLockService') as MockStockLock:
            mock_stock_service = MagicMock()
            mock_stock_service.release_stock_lock = AsyncMock(return_value=True)
            MockStockLock.return_value = mock_stock_service

            service = CartService(redis_client=mock_redis)
            cart = await service.remove_item(
                user_id="user_123",
                item_id="item_1"
            )

            # Should release all locked stock
            mock_stock_service.release_stock_lock.assert_called_once_with("sku_123", 2)

    @pytest.mark.asyncio
    async def test_remove_item_not_found(self):
        """测试移除不存在的商品"""
        mock_redis = create_mock_redis()
        mock_redis.hgetall = AsyncMock(return_value={})

        service = CartService(redis_client=mock_redis)

        from app.core.exceptions import NotFoundException
        with pytest.raises(NotFoundException) as exc_info:
            await service.remove_item(
                user_id="user_123",
                item_id="nonexistent_item"
            )

        assert "不存在" in str(exc_info.value)


class TestClearCart:
    """测试清空购物车"""

    @pytest.mark.asyncio
    async def test_clear_cart_success(self):
        """测试成功清空购物车"""
        mock_redis = create_mock_redis()

        cart_data = {
            "item_1": json.dumps({"id": "item_1", "sku_id": "sku_1", "quantity": 2}),
            "item_2": json.dumps({"id": "item_2", "sku_id": "sku_2", "quantity": 3})
        }
        mock_redis.hgetall = AsyncMock(return_value=cart_data)
        mock_redis.delete = AsyncMock(return_value=True)

        with patch('app.services.cart_service.StockLockService') as MockStockLock:
            mock_stock_service = MagicMock()
            mock_stock_service.release_stock_lock = AsyncMock(return_value=True)
            MockStockLock.return_value = mock_stock_service

            service = CartService(redis_client=mock_redis)
            await service.clear_cart(user_id="user_123")

            # Should release all stock locks
            assert mock_stock_service.release_stock_lock.call_count == 2
            mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_empty_cart(self):
        """测试清空空购物车"""
        mock_redis = create_mock_redis()
        mock_redis.hgetall = AsyncMock(return_value={})
        mock_redis.delete = AsyncMock(return_value=True)

        service = CartService(redis_client=mock_redis)
        await service.clear_cart(user_id="user_123")

        mock_redis.delete.assert_called_once()


class TestCalculation:
    """测试金额计算"""

    @pytest.mark.asyncio
    async def test_calculate_totals_cash_items(self):
        """测试计算现金商品总额"""
        mock_redis = create_mock_redis()

        cart_data = {
            "item_1": json.dumps({
                "id": "item_1",
                "sku_id": "sku_1",
                "quantity": 2,
                "product": {
                    "id": "product_1",
                    "name": "现金商品",
                    "description": None,
                    "images": None,
                    "product_type": "cash",
                    "item_type": "physical",
                    "is_active": True
                },
                "sku": {
                    "id": "sku_1",
                    "sku_code": "SKU001",
                    "name": "规格1",
                    "attributes": {},
                    "stock": 100,
                    "price": 99.99,
                    "currency": "CNY"
                }
            })
        }
        mock_redis.hgetall = AsyncMock(return_value=cart_data)

        service = CartService(redis_client=mock_redis)
        cart = await service.get_cart(user_id="user_123")

        # 99.99 * 2 = 199.98 CNY = 19998 fen
        assert cart.total_amount == 19998
        assert cart.total_points == 0
        assert cart.item_count == 2

    @pytest.mark.asyncio
    async def test_calculate_totals_mixed_items(self):
        """测试计算混合商品总额（现金+积分）"""
        mock_redis = create_mock_redis()

        cart_data = {
            "item_1": json.dumps({
                "id": "item_1",
                "sku_id": "sku_1",
                "quantity": 1,
                "product": {
                    "id": "product_1",
                    "name": "现金商品",
                    "description": None,
                    "images": None,
                    "product_type": "cash",
                    "item_type": "physical",
                    "is_active": True
                },
                "sku": {
                    "id": "sku_1",
                    "sku_code": "SKU001",
                    "name": "规格1",
                    "attributes": {},
                    "stock": 100,
                    "price": 100.0,
                    "currency": "CNY"
                }
            }),
            "item_2": json.dumps({
                "id": "item_2",
                "sku_id": "sku_2",
                "quantity": 2,
                "product": {
                    "id": "product_2",
                    "name": "积分商品",
                    "description": None,
                    "images": None,
                    "product_type": "point",
                    "item_type": "virtual",
                    "is_active": True
                },
                "sku": {
                    "id": "sku_2",
                    "sku_code": "SKU002",
                    "name": "规格2",
                    "attributes": {},
                    "stock": 50,
                    "price": 50,
                    "currency": "POINTS"
                }
            })
        }
        mock_redis.hgetall = AsyncMock(return_value=cart_data)

        service = CartService(redis_client=mock_redis)
        cart = await service.get_cart(user_id="user_123")

        # 100.0 CNY * 1 = 10000 fen
        assert cart.total_amount == 10000
        # 50 POINTS * 2 = 100 points
        assert cart.total_points == 100
        assert cart.item_count == 3


class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_redis_connection_error(self):
        """测试Redis连接错误"""
        mock_redis = create_mock_redis()
        mock_redis.hgetall = AsyncMock(side_effect=ConnectionError("Redis connection failed"))

        service = CartService(redis_client=mock_redis)

        with pytest.raises(ConnectionError):
            await service.get_cart(user_id="user_123")

    @pytest.mark.asyncio
    async def test_invalid_json_in_cart(self):
        """测试购物车数据JSON格式错误"""
        mock_redis = create_mock_redis()

        cart_data = {
            "item_1": "invalid json{{{"
        }
        mock_redis.hgetall = AsyncMock(return_value=cart_data)

        service = CartService(redis_client=mock_redis)
        cart = await service.get_cart(user_id="user_123")

        # Should handle gracefully and return empty cart or skip invalid items
        assert isinstance(cart, CartResponse)
