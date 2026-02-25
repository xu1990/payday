"""
BundleProduct Service 测试 - 套餐商品管理服务

测试覆盖：
1. create_pre_configured_bundle - 创建预配置套餐（成功、商品不存在、SKU不存在、重复商品）
2. create_custom_bundle - 创建自定义套餐（成功、用户不存在、商品列表为空、商品不存在）
3. get_bundle_components - 获取套餐组件（成功、套餐不存在、无组件）
4. calculate_bundle_price - 计算套餐价格（成功、套餐不存在、无价格）
5. validate_bundle_stock - 验证套餐库存（成功、套餐不存在、库存不足）
6. update_bundle_stock - 更新套餐库存（成功、套餐不存在、库存不足、事务回滚）
7. 边界情况测试（空组件、无效数量、负库存）
8. 并发测试
9. 错误处理
"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.product import Product, ProductBundle, ProductPrice, ProductSKU
from app.models.user import User
from app.services.bundle_service import BundleProductService
from sqlalchemy.exc import DatabaseError, IntegrityError


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
    mock_redis.decr = AsyncMock()
    mock_redis.expire = AsyncMock()
    mock_redis.eval = AsyncMock()
    mock_redis.exists = AsyncMock()
    return mock_redis


def setup_mock_bundle_components(mock_db, bundles):
    """
    设置mock数据库用于get_bundle_components

    Args:
        mock_db: Mock数据库
        bundles: ProductBundle对象列表
    """
    mock_results = []

    # 第一个查询：获取bundles
    mock_bundle_result = MagicMock()
    mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles
    mock_results.append(mock_bundle_result)

    # 为每个bundle设置SKU和Product查询
    for bundle in bundles:
        # SKU查询
        if bundle.component_sku_id:
            mock_sku_result = MagicMock()
            mock_sku_result.unique.return_value.scalars.return_value.first.return_value = None
            mock_results.append(mock_sku_result)

        # Product查询
        mock_product_result = MagicMock()
        mock_product_result.unique.return_value.scalars.return_value.first.return_value = None
        mock_results.append(mock_product_result)

    mock_db.execute.side_effect = mock_results


def create_mock_db():
    """创建mock数据库session"""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.merge = MagicMock()
    return mock_db


def create_mock_user(user_id: str, username: str = "testuser"):
    """创建mock用户对象"""
    user = MagicMock()
    user.id = user_id
    user.username = username
    user.nickname = "测试用户"
    user.avatar_url = "https://example.com/avatar.jpg"
    user.created_at = datetime.utcnow()
    return user


def create_mock_product(product_id: str, name: str, item_type: str = "bundle", bundle_type: str = "pre_configured"):
    """创建mock商品对象"""
    product = MagicMock()
    product.id = product_id
    product.name = name
    product.description = f"{name}描述"
    product.images = ["https://example.com/image.jpg"]
    product.category_id = "category_123"
    product.product_type = "point"
    product.item_type = item_type
    product.bundle_type = bundle_type
    product.is_active = True
    product.is_virtual = False
    product.sort_order = 0
    product.seo_keywords = "套餐,测试"
    product.created_at = datetime.utcnow()
    product.updated_at = datetime.utcnow()
    return product


def create_mock_sku(sku_id: str, product_id: str, stock: int = 100, price: int = 10000):
    """创建mock SKU对象"""
    sku = MagicMock()
    sku.id = sku_id
    sku.product_id = product_id
    sku.sku_code = f"SKU_{sku_id[-8:]}"
    sku.name = "默认规格"
    sku.attributes = {}
    sku.stock = stock
    sku.stock_unlimited = False
    sku.images = None
    sku.weight_grams = None
    sku.is_active = True
    sku.created_at = datetime.utcnow()
    return sku


def create_mock_product_price(sku_id: str, price_amount: int, currency: str = "POINTS"):
    """创建mock价格对象"""
    price = MagicMock()
    price.id = f"price_{sku_id[-8:]}"
    price.sku_id = sku_id
    price.price_type = "base"
    price.price_amount = price_amount
    price.currency = currency
    price.min_quantity = 1
    price.membership_level = None
    price.valid_from = None
    price.valid_until = None
    price.is_active = True
    price.created_at = datetime.utcnow()
    return price


def create_mock_bundle(bundle_id: str, bundle_product_id: str, component_product_id: str,
                       component_sku_id: str, quantity: int = 1):
    """创建mock套餐组件对象"""
    bundle = MagicMock()
    bundle.id = bundle_id
    bundle.bundle_product_id = bundle_product_id
    bundle.component_product_id = component_product_id
    bundle.component_sku_id = component_sku_id
    bundle.quantity = quantity
    bundle.is_required = True
    return bundle


class TestBundleProductService:
    """BundleProductService测试类"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        redis_client = create_mock_redis()
        return BundleProductService(redis_client=redis_client)

    @pytest.fixture
    def mock_db(self):
        """创建mock数据库"""
        return create_mock_db()

    # ==================== create_pre_configured_bundle 测试 ====================

    @pytest.mark.asyncio
    async def test_create_pre_configured_bundle_success(self, service, mock_db):
        """测试：成功创建预配置套餐"""
        bundle_product_id = "bundle_123"
        component_data = [
            {"bundle_product_id": bundle_product_id, "product_id": "prod_1", "sku_id": "sku_1", "quantity": 2},
            {"bundle_product_id": bundle_product_id, "product_id": "prod_2", "sku_id": "sku_2", "quantity": 1},
        ]

        # Mock商品和SKU存在
        bundle_product = create_mock_product(bundle_product_id, "测试套餐")
        component_1 = create_mock_product("prod_1", "组件1")
        component_2 = create_mock_product("prod_2", "组件2")
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=50)
        sku_2 = create_mock_sku("sku_2", "prod_2", stock=30)

        # 设置查询结果序列
        mock_results = []
        for product in [bundle_product, component_1, component_2]:
            mock_result = MagicMock()
            mock_result.unique.return_value.scalars.return_value.first.return_value = product
            mock_results.append(mock_result)

        for sku in [sku_1, sku_2]:
            mock_result = MagicMock()
            mock_result.unique.return_value.scalars.return_value.first.return_value = sku
            mock_results.append(mock_result)

        mock_db.execute.side_effect = mock_results

        # 执行
        result = await service.create_pre_configured_bundle(mock_db, component_data)

        # 验证
        assert result is True
        assert mock_db.add.call_count == 2  # 添加2个组件
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_pre_configured_bundle_bundle_product_not_found(self, service, mock_db):
        """测试：套餐商品不存在"""
        bundle_product_id = "bundle_999"
        component_data = [{"bundle_product_id": bundle_product_id, "product_id": "prod_1", "sku_id": "sku_1", "quantity": 1}]

        # Mock套餐商品不存在
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        # 执行并验证异常
        with pytest.raises(NotFoundException) as exc_info:
            await service.create_pre_configured_bundle(mock_db, component_data)

        assert "套餐商品不存在" in str(exc_info.value)
        assert exc_info.value.code == "BUNDLE_PRODUCT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_create_pre_configured_bundle_component_not_found(self, service, mock_db):
        """测试：组件商品不存在"""
        bundle_product_id = "bundle_123"
        component_data = [{"bundle_product_id": bundle_product_id, "product_id": "prod_999", "sku_id": "sku_1", "quantity": 1}]

        # Mock套餐商品存在，但组件不存在
        bundle_product = create_mock_product(bundle_product_id, "测试套餐")

        mock_results = []
        mock_result1 = MagicMock()
        mock_result1.unique.return_value.scalars.return_value.first.return_value = bundle_product
        mock_results.append(mock_result1)

        mock_result2 = MagicMock()
        mock_result2.unique.return_value.scalars.return_value.first.return_value = None
        mock_results.append(mock_result2)

        mock_db.execute.side_effect = mock_results

        # 执行并验证异常
        with pytest.raises(NotFoundException) as exc_info:
            await service.create_pre_configured_bundle(mock_db, component_data)

        assert "组件商品不存在" in str(exc_info.value)
        assert exc_info.value.code == "COMPONENT_PRODUCT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_create_pre_configured_bundle_sku_not_found(self, service, mock_db):
        """测试：组件SKU不存在"""
        bundle_product_id = "bundle_123"
        component_data = [{"product_id": "prod_1", "sku_id": "sku_999", "quantity": 1}]

        # Mock商品存在，但SKU不存在
        bundle_product = create_mock_product(bundle_product_id, "测试套餐")
        component_1 = create_mock_product("prod_1", "组件1")

        mock_results = []
        mock_result1 = MagicMock()
        mock_result1.unique.return_value.scalars.return_value.first.return_value = bundle_product
        mock_results.append(mock_result1)

        mock_result2 = MagicMock()
        mock_result2.unique.return_value.scalars.return_value.first.return_value = component_1
        mock_results.append(mock_result2)

        mock_result3 = MagicMock()
        mock_result3.unique.return_value.scalars.return_value.first.return_value = None
        mock_results.append(mock_result3)

        mock_db.execute.side_effect = mock_results

        # 执行并验证异常
        with pytest.raises(NotFoundException) as exc_info:
            await service.create_pre_configured_bundle(mock_db, component_data)

        assert "SKU不存在" in str(exc_info.value)
        assert exc_info.value.code == "SKU_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_create_pre_configured_bundle_empty_components(self, service, mock_db):
        """测试：组件列表为空"""
        component_data = []

        # 执行并验证异常
        with pytest.raises(ValidationException) as exc_info:
            await service.create_pre_configured_bundle(mock_db, component_data)

        assert "组件列表不能为空" in str(exc_info.value)
        assert exc_info.value.code == "EMPTY_COMPONENTS"

    @pytest.mark.asyncio
    async def test_create_pre_configured_bundle_invalid_quantity(self, service, mock_db):
        """测试：无效的数量"""
        bundle_product_id = "bundle_123"
        component_data = [{"product_id": "prod_1", "sku_id": "sku_1", "quantity": 0}]

        # 执行并验证异常
        with pytest.raises(ValidationException) as exc_info:
            await service.create_pre_configured_bundle(mock_db, component_data)

        assert "数量必须大于0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_pre_configured_bundle_transaction_rollback(self, service, mock_db):
        """测试：创建失败时事务回滚"""
        bundle_product_id = "bundle_123"
        component_data = [{"product_id": "prod_1", "sku_id": "sku_1", "quantity": 1}]

        # Mock数据库操作失败
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = MagicMock()
        mock_db.execute.return_value = mock_result
        mock_db.commit.side_effect = DatabaseError("Connection lost", {}, None)

        # 执行并验证异常
        with pytest.raises(DatabaseError):
            await service.create_pre_configured_bundle(mock_db, component_data)

        # 验证回滚被调用
        mock_db.rollback.assert_called_once()

    # ==================== create_custom_bundle 测试 ====================

    @pytest.mark.asyncio
    async def test_create_custom_bundle_success(self, service, mock_db):
        """测试：成功创建自定义套餐"""
        user_id = "user_123"
        bundle_name = "我的自定义套餐"
        items = [
            {"product_id": "prod_1", "sku_id": "sku_1", "quantity": 1},
            {"product_id": "prod_2", "sku_id": "sku_2", "quantity": 2},
        ]

        # Mock用户存在
        user = create_mock_user(user_id)

        # Mock组件商品和SKU
        component_1 = create_mock_product("prod_1", "组件1")
        component_2 = create_mock_product("prod_2", "组件2")
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=50)
        sku_2 = create_mock_sku("sku_2", "prod_2", stock=30)

        # 设置查询结果序列
        mock_results = []
        # User查询
        mock_result_user = MagicMock()
        mock_result_user.unique.return_value.scalars.return_value.first.return_value = user
        mock_results.append(mock_result_user)

        for product in [component_1, component_2]:
            mock_result = MagicMock()
            mock_result.unique.return_value.scalars.return_value.first.return_value = product
            mock_results.append(mock_result)

        for sku in [sku_1, sku_2]:
            mock_result = MagicMock()
            mock_result.unique.return_value.scalars.return_value.first.return_value = sku
            mock_results.append(mock_result)

        mock_db.execute.side_effect = mock_results

        # 执行
        result = await service.create_custom_bundle(mock_db, user_id, bundle_name, items)

        # 验证
        assert result is not None
        assert "id" in result
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_custom_bundle_user_not_found(self, service, mock_db):
        """测试：用户不存在"""
        user_id = "user_999"
        bundle_name = "我的套餐"
        items = [{"product_id": "prod_1", "sku_id": "sku_1", "quantity": 1}]

        # Mock用户不存在
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        # 执行并验证异常
        with pytest.raises(NotFoundException) as exc_info:
            await service.create_custom_bundle(mock_db, user_id, bundle_name, items)

        assert "用户不存在" in str(exc_info.value)
        assert exc_info.value.code == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_create_custom_bundle_empty_items(self, service, mock_db):
        """测试：商品列表为空"""
        user_id = "user_123"
        bundle_name = "我的套餐"
        items = []

        # 执行并验证异常
        with pytest.raises(ValidationException) as exc_info:
            await service.create_custom_bundle(mock_db, user_id, bundle_name, items)

        assert "商品列表不能为空" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_custom_bundle_too_many_items(self, service, mock_db):
        """测试：商品数量超限"""
        user_id = "user_123"
        bundle_name = "我的套餐"
        items = [{"product_id": f"prod_{i}", "sku_id": f"sku_{i}", "quantity": 1} for i in range(21)]

        # 执行并验证异常
        with pytest.raises(ValidationException) as exc_info:
            await service.create_custom_bundle(mock_db, user_id, bundle_name, items)

        assert "商品数量不能超过" in str(exc_info.value)

    # ==================== get_bundle_components 测试 ====================

    @pytest.mark.asyncio
    async def test_get_bundle_components_success(self, service, mock_db):
        """测试：成功获取套餐组件"""
        bundle_product_id = "bundle_123"

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 2),
            create_mock_bundle("bundle_2", bundle_product_id, "prod_2", "sku_2", 1),
        ]

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = bundles
        mock_db.execute.return_value = mock_result

        # 执行
        components = await service.get_bundle_components(mock_db, bundle_product_id)

        # 验证
        assert len(components) == 2
        assert components[0]["component_product_id"] == "prod_1"
        assert components[0]["quantity"] == 2

    @pytest.mark.asyncio
    async def test_get_bundle_components_empty(self, service, mock_db):
        """测试：套餐无组件"""
        bundle_product_id = "bundle_123"

        # Mock空组件列表
        setup_mock_bundle_components(mock_db, [])

        # 执行
        components = await service.get_bundle_components(mock_db, bundle_product_id)

        # 验证
        assert len(components) == 0

        # 执行
    # ==================== calculate_bundle_price 测试 ====================

    @pytest.mark.asyncio
    async def test_calculate_bundle_price_success(self, service, mock_db):
        """测试：成功计算套餐价格"""
        bundle_product_id = "bundle_123"

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 2),
            create_mock_bundle("bundle_2", bundle_product_id, "prod_2", "sku_2", 1),
        ]

        # Mock价格
        prices = [
            create_mock_product_price("sku_1", 5000),  # 50元 * 2 = 100元
            create_mock_product_price("sku_2", 8000),  # 80元 * 1 = 80元
        ]

        # 设置查询结果
        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_price_results = []
        for price in prices:
            mock_result = MagicMock()
            mock_result.unique.return_value.scalars.return_value.first.return_value = price
            mock_price_results.append(mock_result)

        mock_db.execute.side_effect = [mock_bundle_result] + mock_price_results

        # 执行
        total_price = await service.calculate_bundle_price(mock_db, bundle_product_id)

        # 验证：5000 * 2 + 8000 * 1 = 18000
        assert total_price == 18000

    @pytest.mark.asyncio
    async def test_calculate_bundle_price_no_components(self, service, mock_db):
        """测试：套餐无组件时价格为0"""
        bundle_product_id = "bundle_123"

        # Mock空组件列表
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # 执行
        total_price = await service.calculate_bundle_price(mock_db, bundle_product_id)

        # 验证
        assert total_price == 0

    @pytest.mark.asyncio
    async def test_calculate_bundle_price_no_price_found(self, service, mock_db):
        """测试：组件无价格时抛出异常"""
        bundle_product_id = "bundle_123"

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 1),
        ]

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_price_result = MagicMock()
        mock_price_result.unique.return_value.scalars.return_value.first.return_value = None

        mock_db.execute.side_effect = [mock_bundle_result, mock_price_result]

        # 执行并验证异常
        with pytest.raises(BusinessException) as exc_info:
            await service.calculate_bundle_price(mock_db, bundle_product_id)

        assert "未找到价格信息" in str(exc_info.value)

    # ==================== validate_bundle_stock 测试 ====================

    @pytest.mark.asyncio
    async def test_validate_bundle_stock_success(self, service, mock_db):
        """测试：成功验证套餐库存"""
        bundle_product_id = "bundle_123"
        quantity = 2

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 2),
            create_mock_bundle("bundle_2", bundle_product_id, "prod_2", "sku_2", 1),
        ]

        # Mock SKU库存
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=100)  # 需要 2*2=4，充足
        sku_2 = create_mock_sku("sku_2", "prod_2", stock=50)   # 需要 1*2=2，充足

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_sku_results = []
        for sku in [sku_1, sku_2]:
            mock_result = MagicMock()
            mock_result.unique.return_value.scalars.return_value.first.return_value = sku
            mock_sku_results.append(mock_result)

        mock_db.execute.side_effect = [mock_bundle_result] + mock_sku_results

        # 执行
        is_valid = await service.validate_bundle_stock(mock_db, bundle_product_id, quantity)

        # 验证
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_bundle_stock_insufficient(self, service, mock_db):
        """测试：库存不足"""
        bundle_product_id = "bundle_123"
        quantity = 10

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 2),
        ]

        # Mock SKU库存不足
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=15)  # 需要 2*10=20，库存不足

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_sku_result = MagicMock()
        mock_sku_result.unique.return_value.scalars.return_value.first.return_value = sku_1

        mock_db.execute.side_effect = [mock_bundle_result, mock_sku_result]

        # 执行并验证异常
        with pytest.raises(BusinessException) as exc_info:
            await service.validate_bundle_stock(mock_db, bundle_product_id, quantity)

        assert "库存不足" in str(exc_info.value)
        assert exc_info.value.code == "INSUFFICIENT_STOCK"

    @pytest.mark.asyncio
    async def test_validate_bundle_stock_unlimited_stock(self, service, mock_db):
        """测试：无限库存SKU"""
        bundle_product_id = "bundle_123"
        quantity = 1000

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 1),
        ]

        # Mock无限库存SKU
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=0)
        sku_1.stock_unlimited = True

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_sku_result = MagicMock()
        mock_sku_result.unique.return_value.scalars.return_value.first.return_value = sku_1

        mock_db.execute.side_effect = [mock_bundle_result, mock_sku_result]

        # 执行
        is_valid = await service.validate_bundle_stock(mock_db, bundle_product_id, quantity)

        # 验证
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_bundle_stock_no_components(self, service, mock_db):
        """测试：套餐无组件"""
        bundle_product_id = "bundle_123"
        quantity = 1

        # Mock空组件列表
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # 执行
        is_valid = await service.validate_bundle_stock(mock_db, bundle_product_id, quantity)

        # 验证
        assert is_valid is True

    # ==================== update_bundle_stock 测试 ====================

    @pytest.mark.asyncio
    async def test_update_bundle_stock_success(self, service, mock_db):
        """测试：成功更新套餐库存"""
        bundle_product_id = "bundle_123"
        quantity = 2  # 减少2个套餐

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 2),
            create_mock_bundle("bundle_2", bundle_product_id, "prod_2", "sku_2", 1),
        ]

        # Mock SKU
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=100)
        sku_2 = create_mock_sku("sku_2", "prod_2", stock=50)

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_sku_results = []
        for sku in [sku_1, sku_2]:
            mock_result = MagicMock()
            mock_result.unique.return_value.scalars.return_value.first.return_value = sku
            mock_sku_results.append(mock_result)

        mock_db.execute.side_effect = [mock_bundle_result] + mock_sku_results

        # 执行
        result = await service.update_bundle_stock(mock_db, bundle_product_id, quantity)

        # 验证
        assert result is True
        # sku_1: 100 - 2*2 = 96
        # sku_2: 50 - 1*2 = 48
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_bundle_stock_insufficient(self, service, mock_db):
        """测试：更新库存时库存不足"""
        bundle_product_id = "bundle_123"
        quantity = 10

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 2),
        ]

        # Mock SKU库存不足
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=15)

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_sku_result = MagicMock()
        mock_sku_result.unique.return_value.scalars.return_value.first.return_value = sku_1

        mock_db.execute.side_effect = [mock_bundle_result, mock_sku_result]

        # 执行并验证异常
        with pytest.raises(BusinessException) as exc_info:
            await service.update_bundle_stock(mock_db, bundle_product_id, quantity)

        assert "库存不足" in str(exc_info.value)
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_bundle_stock_increase(self, service, mock_db):
        """测试：增加库存（负quantity）"""
        bundle_product_id = "bundle_123"
        quantity = -2  # 增加2个套餐（订单取消等场景）

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 2),
        ]

        # Mock SKU
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=100)

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_sku_result = MagicMock()
        mock_sku_result.unique.return_value.scalars.return_value.first.return_value = sku_1

        mock_db.execute.side_effect = [mock_bundle_result, mock_sku_result]

        # 执行
        result = await service.update_bundle_stock(mock_db, bundle_product_id, quantity)

        # 验证
        assert result is True
        # 库存应增加：100 - (2 * -2) = 104

    @pytest.mark.asyncio
    async def test_update_bundle_stock_unlimited_stock(self, service, mock_db):
        """测试：无限库存SKU不更新"""
        bundle_product_id = "bundle_123"
        quantity = 10

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 1),
        ]

        # Mock无限库存SKU
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=0)
        sku_1.stock_unlimited = True

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_sku_result = MagicMock()
        mock_sku_result.unique.return_value.scalars.return_value.first.return_value = sku_1

        mock_db.execute.side_effect = [mock_bundle_result, mock_sku_result]

        # 执行
        result = await service.update_bundle_stock(mock_db, bundle_product_id, quantity)

        # 验证
        assert result is True
        # 无限库存SKU不应被更新
        assert sku_1.stock == 0

    @pytest.mark.asyncio
    async def test_update_bundle_stock_transaction_rollback(self, service, mock_db):
        """测试：更新失败时事务回滚"""
        bundle_product_id = "bundle_123"
        quantity = 1

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 1),
        ]

        # Mock SKU
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=100)

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_sku_result = MagicMock()
        mock_sku_result.unique.return_value.scalars.return_value.first.return_value = sku_1

        mock_db.execute.side_effect = [mock_bundle_result, mock_sku_result]
        mock_db.commit.side_effect = DatabaseError("Connection lost", {}, None)

        # 执行并验证异常
        with pytest.raises(DatabaseError):
            await service.update_bundle_stock(mock_db, bundle_product_id, quantity)

        # 验证回滚被调用
        mock_db.rollback.assert_called_once()

    # ==================== 边界情况测试 ====================

    @pytest.mark.asyncio
    async def test_calculate_bundle_price_with_multiple_prices(self, service, mock_db):
        """测试：多个价格类型时使用base价格"""
        bundle_product_id = "bundle_123"

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 1),
        ]

        # Mock多个价格
        base_price = create_mock_product_price("sku_1", 5000)
        base_price.price_type = "base"
        member_price = create_mock_product_price("sku_1", 4000)
        member_price.price_type = "member"

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_price_result = MagicMock()
        # 返回base价格
        mock_price_result.unique.return_value.scalars.return_value.first.return_value = base_price

        mock_db.execute.side_effect = [mock_bundle_result, mock_price_result]

        # 执行
        total_price = await service.calculate_bundle_price(mock_db, bundle_product_id)

        # 验证：应使用base价格
        assert total_price == 5000

    @pytest.mark.asyncio
    async def test_create_pre_configured_bundle_with_required_optional(self, service, mock_db):
        """测试：创建套餐时包含必选和可选组件"""
        bundle_product_id = "bundle_123"
        component_data = [
            {"product_id": "prod_1", "sku_id": "sku_1", "quantity": 1, "is_required": True},
            {"product_id": "prod_2", "sku_id": "sku_2", "quantity": 1, "is_required": False},
        ]

        # Mock商品和SKU
        bundle_product = create_mock_product(bundle_product_id, "测试套餐")
        component_1 = create_mock_product("prod_1", "组件1")
        component_2 = create_mock_product("prod_2", "组件2")
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=50)
        sku_2 = create_mock_sku("sku_2", "prod_2", stock=30)

        mock_results = []
        for product in [bundle_product, component_1, component_2]:
            mock_result = MagicMock()
            mock_result.unique.return_value.scalars.return_value.first.return_value = product
            mock_results.append(mock_result)

        for sku in [sku_1, sku_2]:
            mock_result = MagicMock()
            mock_result.unique.return_value.scalars.return_value.first.return_value = sku
            mock_results.append(mock_result)

        mock_db.execute.side_effect = mock_results

        # 执行
        result = await service.create_pre_configured_bundle(mock_db, component_data)

        # 验证
        assert result is True
        assert mock_db.add.call_count == 2

    @pytest.mark.asyncio
    async def test_validate_bundle_stock_with_zero_quantity(self, service, mock_db):
        """测试：验证数量为0时始终有效"""
        bundle_product_id = "bundle_123"
        quantity = 0

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 1),
        ]

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = bundles
        mock_db.execute.return_value = mock_result

        # 执行
        is_valid = await service.validate_bundle_stock(mock_db, bundle_product_id, quantity)

        # 验证：数量为0时不需要检查库存
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_update_bundle_stock_with_zero_quantity(self, service, mock_db):
        """测试：更新数量为0时不做任何操作"""
        bundle_product_id = "bundle_123"
        quantity = 0

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 1),
        ]

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = bundles
        mock_db.execute.return_value = mock_result

        # 执行
        result = await service.update_bundle_stock(mock_db, bundle_product_id, quantity)

        # 验证
        assert result is True
        # 不应执行commit
        mock_db.commit.assert_not_called()

    # ==================== 错误处理测试 ====================

    @pytest.mark.asyncio
    async def test_create_pre_configured_bundle_duplicate_component(self, service, mock_db):
        """测试：重复添加同一组件"""
        bundle_product_id = "bundle_123"
        component_data = [
            {"product_id": "prod_1", "sku_id": "sku_1", "quantity": 1},
            {"product_id": "prod_1", "sku_id": "sku_1", "quantity": 1},  # 重复
        ]

        # Mock商品和SKU
        bundle_product = create_mock_product(bundle_product_id, "测试套餐")
        component_1 = create_mock_product("prod_1", "组件1")
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=50)

        mock_results = []
        mock_result1 = MagicMock()
        mock_result1.unique.return_value.scalars.return_value.first.return_value = bundle_product
        mock_results.append(mock_result1)

        mock_result2 = MagicMock()
        mock_result2.unique.return_value.scalars.return_value.first.return_value = component_1
        mock_results.append(mock_result2)

        mock_result3 = MagicMock()
        mock_result3.unique.return_value.scalars.return_value.first.return_value = sku_1
        mock_results.append(mock_result3)

        mock_result4 = MagicMock()
        mock_result4.unique.return_value.scalars.return_value.first.return_value = component_1
        mock_results.append(mock_result4)

        mock_result5 = MagicMock()
        mock_result5.unique.return_value.scalars.return_value.first.return_value = sku_1
        mock_results.append(mock_result5)

        mock_db.execute.side_effect = mock_results

        # 执行 - 应该允许重复（可能是用户想要多个相同的组件）
        result = await service.create_pre_configured_bundle(mock_db, component_data)

        # 验证
        assert result is True
        assert mock_db.add.call_count == 2

    @pytest.mark.asyncio
    async def test_calculate_bundle_price_with_invalid_currency(self, service, mock_db):
        """测试：混合货币类型的套餐"""
        bundle_product_id = "bundle_123"

        # Mock套餐组件
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 1),
            create_mock_bundle("bundle_2", bundle_product_id, "prod_2", "sku_2", 1),
        ]

        # Mock不同货币的价格
        price_points = create_mock_product_price("sku_1", 5000, "POINTS")
        price_cny = create_mock_product_price("sku_2", 8000, "CNY")

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_price_result1 = MagicMock()
        mock_price_result1.unique.return_value.scalars.return_value.first.return_value = price_points

        mock_price_result2 = MagicMock()
        mock_price_result2.unique.return_value.scalars.return_value.first.return_value = price_cny

        mock_db.execute.side_effect = [mock_bundle_result, mock_price_result1, mock_price_result2]

        # 执行并验证异常
        with pytest.raises(BusinessException) as exc_info:
            await service.calculate_bundle_price(mock_db, bundle_product_id)

        assert "货币类型不一致" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_bundle_components_with_inactive_skus(self, service, mock_db):
        """测试：获取套餐组件时过滤非活跃SKU"""
        bundle_product_id = "bundle_123"

        # Mock套餐组件（包含非活跃SKU）
        bundles = [
            create_mock_bundle("bundle_1", bundle_product_id, "prod_1", "sku_1", 1),
            create_mock_bundle("bundle_2", bundle_product_id, "prod_2", "sku_2", 1),
        ]

        # Mock SKU（一个活跃，一个非活跃）
        sku_1 = create_mock_sku("sku_1", "prod_1", stock=50)
        sku_1.is_active = True

        sku_2 = create_mock_sku("sku_2", "prod_2", stock=30)
        sku_2.is_active = False

        mock_bundle_result = MagicMock()
        mock_bundle_result.unique.return_value.scalars.return_value.all.return_value = bundles

        mock_sku_results = []
        for sku in [sku_1, sku_2]:
            mock_result = MagicMock()
            mock_result.unique.return_value.scalars.return_value.first.return_value = sku
            mock_sku_results.append(mock_result)

        mock_db.execute.side_effect = [mock_bundle_result] + mock_sku_results

        # 执行
        components = await service.get_bundle_components(mock_db, bundle_product_id)

        # 验证：应只返回活跃的组件
        assert len(components) == 1
        assert components[0]["component_sku_id"] == "sku_1"
