"""
购物车 API 集成测试
Shopping Cart API Integration Tests

测试购物车相关的所有API端点：
- GET /cart - 获取购物车
- POST /cart/items - 添加商品到购物车
- PUT /cart/items/{item_id} - 更新购物车商品数量
- DELETE /cart/items/{item_id} - 移除购物车商品
- DELETE /cart - 清空购物车
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from app.schemas.cart import CartResponse
from app.core.deps import get_current_user


# Mock get_current_user dependency
async def mock_get_current_user():
    """Mock current user for testing"""
    from app.models.user import User
    user = User(
        id="test-user-123",
        openid="test-openid-123",
        anonymous_name="测试用户",
        nickname="测试用户",
        avatar="https://example.com/avatar.jpg",
        status="normal"
    )
    return user


@pytest.mark.asyncio
async def test_get_empty_cart():
    """测试获取空购物车"""
    # Mock Redis to return empty cart
    mock_redis = MagicMock()
    mock_redis.hgetall = AsyncMock(return_value={})
    mock_redis.expire = AsyncMock(return_value=True)

    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/cart")

            assert response.status_code == 200
            data = response.json()
            assert "details" in data
            assert data["details"]["items"] == []
            assert data["details"]["total_amount"] == 0
            assert data["details"]["total_points"] == 0
            assert data["details"]["item_count"] == 0

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_cart_with_items():
    """测试获取包含商品的购物车"""
    # Mock Redis to return cart with items
    import json

    mock_redis = MagicMock()
    cart_item = {
        "id": "item-123",
        "sku_id": "sku-123",
        "quantity": 2,
        "product": {
            "id": "prod-123",
            "name": "测试商品",
            "description": "测试描述",
            "images": ["image1.jpg"],
            "product_type": "virtual",
            "item_type": "points",
            "is_active": True
        },
        "sku": {
            "id": "sku-123",
            "sku_code": "SKU001",
            "name": "100积分",
            "attributes": {"amount": 100},
            "stock": 100,
            "price": 10.0,
            "currency": "POINTS"
        }
    }
    mock_redis.hgetall = AsyncMock(return_value={
        "sku-123": json.dumps(cart_item, ensure_ascii=False)
    })
    mock_redis.expire = AsyncMock(return_value=True)

    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/cart")

            assert response.status_code == 200
            data = response.json()
            assert "details" in data
            assert len(data["details"]["items"]) == 1
            assert data["details"]["items"][0]["sku_id"] == "sku-123"
            assert data["details"]["items"][0]["quantity"] == 2
            assert data["details"]["item_count"] == 2
            assert data["details"]["total_points"] == 20  # 10 * 2

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_add_item_to_cart(db_session: AsyncSession):
    """测试添加商品到购物车 - 新商品"""
    from app.models.product import Product, ProductSKU, ProductPrice
    from app.services.cart_service import CartService
    import uuid

    # 创建测试商品和SKU
    product = Product(
        id=str(uuid.uuid4()),
        name="测试积分商品",
        description="测试商品描述",
        product_type="virtual",
        item_type="points",
        is_active=True,
        images=["test.jpg"]
    )
    db_session.add(product)

    sku = ProductSKU(
        id=str(uuid.uuid4()),
        product_id=product.id,
        sku_code="TEST_SKU_001",
        name="100积分",
        attributes={"amount": 100},
        stock=100,
        is_active=True
    )
    db_session.add(sku)

    price = ProductPrice(
        id=str(uuid.uuid4()),
        sku_id=sku.id,
        price_type="base",
        price_amount=10.0,
        currency="POINTS",
        is_active=True
    )
    db_session.add(price)
    await db_session.commit()

    # Mock Redis
    mock_redis = MagicMock()
    mock_redis.hget = AsyncMock(return_value=None)  # Item not in cart
    mock_redis.hset = AsyncMock(return_value=True)
    mock_redis.hgetall = AsyncMock(return_value={})  # Return empty cart after add
    mock_redis.expire = AsyncMock(return_value=True)

    # Override both dependencies
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = mock_get_current_user

    from app.core.deps import get_db
    app.dependency_overrides[get_db] = override_get_db

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        with patch.object(CartService, '_get_sku', return_value=sku):
            with patch.object(CartService, '_get_product', return_value=product):
                with patch.object(CartService, '_get_sku_price', return_value={"price": 10.0, "currency": "POINTS"}):
                    with patch('app.services.stock_lock.StockLockService.acquire_stock_lock', AsyncMock(return_value=True)):
                        transport = ASGITransport(app=app)
                        async with AsyncClient(transport=transport, base_url="http://test") as client:
                            response = await client.post(
                                "/api/v1/cart/items",
                                json={"sku_id": sku.id, "quantity": 2}
                            )

                            assert response.status_code == 200
                            data = response.json()
                            assert "details" in data
                            # Verify the response structure

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_add_item_insufficient_stock(db_session: AsyncSession):
    """测试添加商品到购物车 - 库存不足"""
    from app.models.product import Product, ProductSKU, ProductPrice
    from app.services.cart_service import CartService
    from app.core.exceptions import BusinessException
    import uuid

    # 创建测试商品和SKU
    product = Product(
        id=str(uuid.uuid4()),
        name="测试积分商品",
        description="测试商品描述",
        product_type="virtual",
        item_type="points",
        is_active=True,
        images=["test.jpg"]
    )
    db_session.add(product)

    sku = ProductSKU(
        id=str(uuid.uuid4()),
        product_id=product.id,
        sku_code="TEST_SKU_002",
        name="100积分",
        attributes={"amount": 100},
        stock=5,  # Low stock
        is_active=True
    )
    db_session.add(sku)

    price = ProductPrice(
        id=str(uuid.uuid4()),
        sku_id=sku.id,
        price_type="base",
        price_amount=10.0,
        currency="POINTS",
        is_active=True
    )
    db_session.add(price)
    await db_session.commit()

    # Mock Redis
    mock_redis = MagicMock()
    mock_redis.hget = AsyncMock(return_value=None)
    mock_redis.hset = AsyncMock(return_value=True)
    mock_redis.hgetall = AsyncMock(return_value={})
    mock_redis.expire = AsyncMock(return_value=True)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = mock_get_current_user
    from app.core.deps import get_db
    app.dependency_overrides[get_db] = override_get_db

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        with patch.object(CartService, '_get_sku', return_value=sku):
            with patch.object(CartService, '_get_product', return_value=product):
                with patch.object(CartService, '_get_sku_price', return_value={"price": 10.0, "currency": "POINTS"}):
                    # Mock stock lock failure
                    with patch('app.services.stock_lock.StockLockService.acquire_stock_lock', AsyncMock(return_value=False)):
                        transport = ASGITransport(app=app)
                        async with AsyncClient(transport=transport, base_url="http://test") as client:
                            response = await client.post(
                                "/api/v1/cart/items",
                                json={"sku_id": sku.id, "quantity": 10}  # More than stock
                            )

                            assert response.status_code == 400  # Business error

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_add_item_invalid_quantity():
    """测试添加商品到购物车 - 无效数量"""
    app.dependency_overrides[get_current_user] = mock_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Quantity less than 1
        response = await client.post(
            "/api/v1/cart/items",
            json={"sku_id": "sku-123", "quantity": 0}
        )

        assert response.status_code == 422  # Validation error

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_add_item_sku_not_found(db_session: AsyncSession):
    """测试添加商品到购物车 - SKU不存在"""
    from app.services.cart_service import CartService
    from app.core.exceptions import NotFoundException

    # Mock Redis
    mock_redis = MagicMock()
    mock_redis.hget = AsyncMock(return_value=None)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = mock_get_current_user
    from app.core.deps import get_db
    app.dependency_overrides[get_db] = override_get_db

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        with patch.object(CartService, '_get_sku', side_effect=NotFoundException("SKU不存在")):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/cart/items",
                    json={"sku_id": "nonexistent-sku", "quantity": 1}
                )

                assert response.status_code == 404

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_update_cart_item_quantity():
    """测试更新购物车商品数量"""
    import json

    # Mock Redis to return existing cart item
    mock_redis = MagicMock()
    existing_item = {
        "id": "item-123",
        "sku_id": "sku-123",
        "quantity": 2,
        "product": {
            "id": "prod-123",
            "name": "测试商品",
            "product_type": "virtual",
            "item_type": "points",
            "is_active": True
        },
        "sku": {
            "id": "sku-123",
            "sku_code": "SKU001",
            "name": "100积分",
            "attributes": {},
            "stock": 100,
            "price": 10.0,
            "currency": "POINTS"
        }
    }

    mock_redis.hgetall = AsyncMock(return_value={
        "sku-123": json.dumps(existing_item, ensure_ascii=False)
    })
    mock_redis.hset = AsyncMock(return_value=True)
    mock_redis.expire = AsyncMock(return_value=True)

    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        with patch('app.services.stock_lock.StockLockService.acquire_stock_lock', AsyncMock(return_value=True)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/cart/items/{existing_item['id']}",
                    json={"quantity": 5}
                )

                assert response.status_code == 200
                data = response.json()
                assert "details" in data

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_update_cart_item_not_found():
    """测试更新不存在的购物车商品"""
    # Mock Redis to return empty cart
    mock_redis = MagicMock()
    mock_redis.hgetall = AsyncMock(return_value={})

    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/cart/items/nonexistent-item",
                json={"quantity": 5}
            )

            assert response.status_code == 404

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_update_cart_item_insufficient_stock():
    """测试更新购物车商品数量 - 库存不足"""
    import json

    # Mock Redis
    mock_redis = MagicMock()
    existing_item = {
        "id": "item-123",
        "sku_id": "sku-123",
        "quantity": 2,
        "product": {
            "id": "prod-123",
            "name": "测试商品",
            "product_type": "virtual",
            "item_type": "points",
            "is_active": True
        },
        "sku": {
            "id": "sku-123",
            "sku_code": "SKU001",
            "name": "100积分",
            "attributes": {},
            "stock": 100,
            "price": 10.0,
            "currency": "POINTS"
        }
    }

    mock_redis.hgetall = AsyncMock(return_value={
        "sku-123": json.dumps(existing_item, ensure_ascii=False)
    })
    mock_redis.hset = AsyncMock(return_value=True)
    mock_redis.expire = AsyncMock(return_value=True)

    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        # Mock stock lock failure
        with patch('app.services.stock_lock.StockLockService.acquire_stock_lock', AsyncMock(return_value=False)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/cart/items/{existing_item['id']}",
                    json={"quantity": 100}  # Large quantity
                )

                assert response.status_code == 400

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_remove_cart_item():
    """测试移除购物车商品"""
    import json

    # Mock Redis
    mock_redis = MagicMock()
    existing_item = {
        "id": "item-123",
        "sku_id": "sku-123",
        "quantity": 2,
        "product": {
            "id": "prod-123",
            "name": "测试商品",
            "product_type": "virtual",
            "item_type": "points",
            "is_active": True
        },
        "sku": {
            "id": "sku-123",
            "sku_code": "SKU001",
            "name": "100积分",
            "attributes": {},
            "stock": 100,
            "price": 10.0,
            "currency": "POINTS"
        }
    }

    mock_redis.hgetall = AsyncMock(return_value={
        "sku-123": json.dumps(existing_item, ensure_ascii=False)
    })
    mock_redis.hdel = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock(return_value=True)

    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        with patch('app.services.stock_lock.StockLockService.release_stock_lock', AsyncMock(return_value=None)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(
                    f"/api/v1/cart/items/{existing_item['id']}"
                )

                assert response.status_code == 200
                data = response.json()
                assert "details" in data

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_remove_cart_item_not_found():
    """测试移除不存在的购物车商品"""
    # Mock Redis to return empty cart
    mock_redis = MagicMock()
    mock_redis.hgetall = AsyncMock(return_value={})

    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                "/api/v1/cart/items/nonexistent-item"
            )

            assert response.status_code == 404

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_clear_cart():
    """测试清空购物车"""
    import json

    # Mock Redis
    mock_redis = MagicMock()
    mock_redis.hgetall = AsyncMock(return_value={
        "sku-123": json.dumps({}, ensure_ascii=False)
    })
    mock_redis.delete = AsyncMock(return_value=1)

    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch('app.core.cache.get_redis_client', AsyncMock(return_value=mock_redis)):
        with patch('app.services.stock_lock.StockLockService.release_stock_lock', AsyncMock(return_value=None)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete("/api/v1/cart")

                assert response.status_code == 200
                data = response.json()
                assert "message" in data

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_cart_unauthorized():
    """测试未认证用户访问购物车"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/cart")

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_cart_item_invalid_quantity():
    """测试更新购物车商品 - 无效数量"""
    app.dependency_overrides[get_current_user] = mock_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Quantity less than 1
        response = await client.put(
            "/api/v1/cart/items/item-123",
            json={"quantity": 0}
        )

        assert response.status_code == 422  # Validation error

    app.dependency_overrides = {}
