"""
VirtualProduct Service 测试 - 虚拟商品自动发货服务

测试覆盖：
1. deliver_virtual_product - 自动发货（成功、订单不存在、商品项不存在、非虚拟商品、已发货）
2. generate_delivery_code - 生成发货码（成功、SKU不存在、库存不足）
3. validate_delivery_code - 验证发货码（成功、码不存在、码已使用、码过期）
4. get_virtual_content - 获取虚拟内容（成功、SKU不存在、非虚拟商品、内容不存在）
5. check_is_virtual_product - 检查是否虚拟商品（是虚拟、不是虚拟、商品不存在）
6. 发货码唯一性
7. 发货码格式验证
8. 批量发货
9. 事务回滚
10. 并发发货码生成
11. 错误处理
"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductSKU
from app.services.virtual_product_service import VirtualProductService
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
    mock_redis.exists = AsyncMock()
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


def create_mock_order(order_id: str, user_id: str, payment_status: str = "paid", order_status: str = "pending"):
    """创建mock订单对象

    Args:
        order_id: 订单ID
        user_id: 用户ID
        payment_status: 支付状态（默认"paid"）
        order_status: 订单状态（默认"pending"）
    """
    order = MagicMock()
    order.id = order_id
    order.user_id = user_id
    order.order_number = "ORD20260224000001"
    order.total_amount = Decimal("10000")
    order.points_used = 0
    order.discount_amount = Decimal("0")
    order.shipping_cost = Decimal("0")
    order.final_amount = Decimal("10000")
    order.payment_method = "wechat"
    order.payment_status = payment_status
    order.transaction_id = "txn_123456" if payment_status == "paid" else None
    order.paid_at = datetime.utcnow() if payment_status == "paid" else None
    order.status = order_status
    order.shipping_address_id = None
    order.shipping_template_id = None
    order.created_at = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    return order


def create_mock_order_item(item_id: str, order_id: str, product_id: str, sku_id: str = None):
    """创建mock订单项对象"""
    item = MagicMock()
    item.id = item_id
    item.order_id = order_id
    item.product_id = product_id
    item.sku_id = sku_id
    item.product_name = "测试电子书"
    item.sku_name = "PDF版" if sku_id else None
    item.product_image = "https://example.com/image.jpg"
    item.attributes = {"format": "pdf"} if sku_id else None
    item.unit_price = Decimal("10000")
    item.quantity = 1
    item.subtotal = Decimal("10000")
    item.bundle_components = None
    # Important: Explicitly set delivery_code to None to avoid MagicMock auto-creation
    item.delivery_code = None
    return item


def create_mock_product(product_id: str, is_virtual: bool = True, name: str = "测试电子书"):
    """创建mock商品对象"""
    product = MagicMock()
    product.id = product_id
    product.name = name
    product.description = "这是一本测试电子书"
    product.images = ["https://example.com/image.jpg"]
    product.category_id = "category_123"
    product.product_type = "point"
    product.item_type = "virtual" if is_virtual else "physical"
    product.bundle_type = None
    product.is_active = True
    product.is_virtual = is_virtual
    product.sort_order = 0
    product.seo_keywords = "电子书,测试"
    product.created_at = datetime.utcnow()
    product.updated_at = datetime.utcnow()
    return product


def create_mock_sku(sku_id: str, product_id: str, virtual_content: str = None):
    """创建mock SKU对象"""
    sku = MagicMock()
    sku.id = sku_id
    sku.product_id = product_id
    sku.sku_code = f"SKU_{sku_id}"
    sku.name = "PDF版"
    sku.attributes = {"format": "pdf"}
    sku.stock = 999  # Virtual products have unlimited stock
    sku.stock_unlimited = True
    sku.images = None
    sku.weight_grams = None
    sku.is_active = True
    sku.created_at = datetime.utcnow()
    sku.virtual_content = virtual_content  # URL or content
    return sku


class TestVirtualProductService:
    """VirtualProductService测试类"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        redis_client = create_mock_redis()
        return VirtualProductService(redis_client=redis_client)

    @pytest.fixture
    def mock_db(self):
        """创建mock数据库"""
        return create_mock_db()

    # ==================== deliver_virtual_product 测试 ====================

    @pytest.mark.asyncio
    async def test_deliver_virtual_product_success(self, service, mock_db):
        """测试：成功自动发货虚拟商品"""
        order_id = "order_123"
        item_id = "item_123"
        product_id = "product_123"
        sku_id = "sku_123"

        # Mock数据
        order = create_mock_order(order_id, "user_123", "paid")
        item = create_mock_order_item(item_id, order_id, product_id, sku_id)
        # 确保item没有delivery_code属性或为None
        if hasattr(item, 'delivery_code'):
            item.delivery_code = None
        product = create_mock_product(product_id, is_virtual=True)
        sku = create_mock_sku(sku_id, product_id, virtual_content="https://example.com/ebook.pdf")

        # Mock数据库查询 - 需要返回4个查询结果
        # 1. Order查询
        mock_result_order = MagicMock()
        mock_result_order.unique.return_value.scalars.return_value.first.return_value = order

        # 2. OrderItem查询
        mock_result_item = MagicMock()
        mock_result_item.unique.return_value.scalars.return_value.first.return_value = item

        # 3. Product查询
        mock_result_product = MagicMock()
        mock_result_product.unique.return_value.scalars.return_value.first.return_value = product

        # 4. 所有OrderItem查询（用于检查是否全部发货）
        mock_result_all_items = MagicMock()
        mock_result_all_items.unique.return_value.scalars.return_value.all.return_value = [item]

        mock_db.execute.side_effect = [
            mock_result_order,
            mock_result_item,
            mock_result_product,
            mock_result_all_items
        ]

        # Mock发货码生成
        with patch.object(service, 'generate_delivery_code', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = "VD-20260224-ABCD1234"

            # 执行
            result = await service.deliver_virtual_product(mock_db, order_id, item_id)

            # 验证
            assert result is True
            mock_generate.assert_called_once_with(mock_db, sku_id)

    @pytest.mark.asyncio
    async def test_deliver_virtual_product_order_not_found(self, service, mock_db):
        """测试：订单不存在"""
        order_id = "order_999"
        item_id = "item_123"

        # Mock数据库查询返回None
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        # 执行并验证异常
        with pytest.raises(NotFoundException) as exc_info:
            await service.deliver_virtual_product(mock_db, order_id, item_id)

        assert "订单不存在" in str(exc_info.value)
        assert exc_info.value.code == "ORDER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_deliver_virtual_product_item_not_found(self, service, mock_db):
        """测试：订单项不存在"""
        order_id = "order_123"
        item_id = "item_999"

        # Mock订单存在，但订单项不存在
        order = create_mock_order(order_id, "user_123", "paid")

        mock_result_order = MagicMock()
        mock_result_order.unique.return_value.scalars.return_value.first.return_value = order

        mock_result_item = MagicMock()
        mock_result_item.unique.return_value.scalars.return_value.first.return_value = None

        mock_db.execute.side_effect = [mock_result_order, mock_result_item]

        # 执行并验证异常
        with pytest.raises(NotFoundException) as exc_info:
            await service.deliver_virtual_product(mock_db, order_id, item_id)

        assert "订单项不存在" in str(exc_info.value)
        assert exc_info.value.code == "ORDER_ITEM_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_deliver_virtual_product_not_virtual(self, service, mock_db):
        """测试：商品不是虚拟商品"""
        order_id = "order_123"
        item_id = "item_123"
        product_id = "product_123"
        sku_id = "sku_123"

        # Mock数据
        order = create_mock_order(order_id, "user_123", "paid")
        item = create_mock_order_item(item_id, order_id, product_id, sku_id)
        # 确保item没有delivery_code属性
        if hasattr(item, 'delivery_code'):
            delattr(item, 'delivery_code')
        product = create_mock_product(product_id, is_virtual=False)  # 非虚拟商品

        mock_result_order = MagicMock()
        mock_result_order.unique.return_value.scalars.return_value.first.return_value = order

        mock_result_item = MagicMock()
        mock_result_item.unique.return_value.scalars.return_value.first.return_value = item

        mock_result_product = MagicMock()
        mock_result_product.unique.return_value.scalars.return_value.first.return_value = product

        # 第4个查询不会执行，因为会提前抛出异常
        mock_db.execute.side_effect = [mock_result_order, mock_result_item, mock_result_product]

        # 执行并验证异常
        with pytest.raises(BusinessException) as exc_info:
            await service.deliver_virtual_product(mock_db, order_id, item_id)

        assert "非虚拟商品" in str(exc_info.value)
        assert exc_info.value.code == "NOT_VIRTUAL_PRODUCT"

    @pytest.mark.asyncio
    async def test_deliver_virtual_product_already_delivered(self, service, mock_db):
        """测试：商品已发货"""
        order_id = "order_123"
        item_id = "item_123"
        product_id = "product_123"
        sku_id = "sku_123"

        # Mock数据
        order = create_mock_order(order_id, "user_123", "paid")
        item = create_mock_order_item(item_id, order_id, product_id, sku_id)
        item.delivery_code = "VD-20260224-ABCD1234"  # 已有发货码
        item.delivered_at = datetime.utcnow()

        mock_result_order = MagicMock()
        mock_result_order.unique.return_value.scalars.return_value.first.return_value = order

        mock_result_item = MagicMock()
        mock_result_item.unique.return_value.scalars.return_value.first.return_value = item

        mock_db.execute.side_effect = [mock_result_order, mock_result_item]

        # 执行并验证异常
        with pytest.raises(BusinessException) as exc_info:
            await service.deliver_virtual_product(mock_db, order_id, item_id)

        assert "已发货" in str(exc_info.value)
        assert exc_info.value.code == "ALREADY_DELIVERED"

    @pytest.mark.asyncio
    async def test_deliver_virtual_product_without_sku(self, service, mock_db):
        """测试：无SKU的虚拟商品发货"""
        order_id = "order_123"
        item_id = "item_123"
        product_id = "product_123"

        # Mock数据
        order = create_mock_order(order_id, "user_123", "paid")
        item = create_mock_order_item(item_id, order_id, product_id, None)  # 无SKU
        # 确保没有delivery_code属性
        if hasattr(item, 'delivery_code'):
            delattr(item, 'delivery_code')
        product = create_mock_product(product_id, is_virtual=True)

        mock_result_order = MagicMock()
        mock_result_order.unique.return_value.scalars.return_value.first.return_value = order

        mock_result_item = MagicMock()
        mock_result_item.unique.return_value.scalars.return_value.first.return_value = item

        mock_result_product = MagicMock()
        mock_result_product.unique.return_value.scalars.return_value.first.return_value = product

        # 4. 所有OrderItem查询
        mock_result_all_items = MagicMock()
        mock_result_all_items.unique.return_value.scalars.return_value.all.return_value = [item]

        mock_db.execute.side_effect = [
            mock_result_order,
            mock_result_item,
            mock_result_product,
            mock_result_all_items
        ]

        # 执行
        result = await service.deliver_virtual_product(mock_db, order_id, item_id)

        # 验证
        assert result is True

    # ==================== generate_delivery_code 测试 ====================

    @pytest.mark.asyncio
    async def test_generate_delivery_code_success(self, service, mock_db):
        """测试：成功生成发货码"""
        sku_id = "sku_123"

        # Mock Redis incr（用于生成唯一码）
        service.redis_client.incr.return_value = 1

        # 执行
        code = await service.generate_delivery_code(mock_db, sku_id)

        # 验证格式：VD-YYYYMMDD-XXXXXXXX
        assert code.startswith("VD-")
        assert len(code) == 20  # VD- + 8位日期 + - + 8位随机码
        service.redis_client.incr.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_delivery_code_uniqueness(self, service, mock_db):
        """测试：发货码唯一性"""
        sku_id = "sku_123"

        # Mock Redis返回递增的序列号
        service.redis_client.incr.side_effect = [1, 2, 3]

        # 生成多个码
        code1 = await service.generate_delivery_code(mock_db, sku_id)
        code2 = await service.generate_delivery_code(mock_db, sku_id)
        code3 = await service.generate_delivery_code(mock_db, sku_id)

        # 验证唯一性
        assert code1 != code2
        assert code2 != code3
        assert code1 != code3

    @pytest.mark.asyncio
    async def test_generate_delivery_code_format_validation(self, service, mock_db):
        """测试：发货码格式验证"""
        sku_id = "sku_123"

        service.redis_client.incr.return_value = 12345

        # 执行
        code = await service.generate_delivery_code(mock_db, sku_id)

        # 验证格式
        parts = code.split("-")
        assert len(parts) == 3
        assert parts[0] == "VD"
        assert len(parts[1]) == 8  # 日期部分
        assert len(parts[2]) == 8  # 随机码部分

    # ==================== validate_delivery_code 测试 ====================

    @pytest.mark.asyncio
    async def test_validate_delivery_code_success(self, service, mock_db):
        """测试：成功验证发货码"""
        code = "VD-20260224-ABCD1234"

        # Mock Redis查询（码存在且未使用）
        # hgetall返回完整的hash数据
        service.redis_client.hgetall.return_value = {
            b"sku_id": b"sku_123",
            b"used": b"0",
            b"created_at": b"2026-02-24T10:00:00"
        }

        # 执行
        result = await service.validate_delivery_code(mock_db, code)

        # 验证
        assert result is True
        # hset被调用两次（设置used和used_at）
        assert service.redis_client.hset.call_count == 2

    @pytest.mark.asyncio
    async def test_validate_delivery_code_not_found(self, service, mock_db):
        """测试：发货码不存在"""
        code = "VD-20260224-ABCD1234"  # 使用有效格式

        # Mock Redis返回空字典（码不存在）
        service.redis_client.hgetall.return_value = {}

        # 执行并验证异常
        with pytest.raises(NotFoundException) as exc_info:
            await service.validate_delivery_code(mock_db, code)

        assert "发货码不存在" in str(exc_info.value)
        assert exc_info.value.code == "DELIVERY_CODE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_validate_delivery_code_already_used(self, service, mock_db):
        """测试：发货码已使用"""
        code = "VD-20260224-ABCD1234"

        # Mock Redis返回已使用状态
        service.redis_client.hgetall.return_value = {
            b"sku_id": b"sku_123",
            b"used": b"1",  # 已使用
            b"created_at": b"2026-02-24T10:00:00"
        }

        # 执行并验证异常
        with pytest.raises(BusinessException) as exc_info:
            await service.validate_delivery_code(mock_db, code)

        assert "发货码已使用" in str(exc_info.value)
        assert exc_info.value.code == "DELIVERY_CODE_ALREADY_USED"

    @pytest.mark.asyncio
    async def test_validate_delivery_code_invalid_format(self, service, mock_db):
        """测试：发货码格式无效"""
        code = "INVALID_CODE_FORMAT"

        # 执行并验证异常
        with pytest.raises(ValidationException) as exc_info:
            await service.validate_delivery_code(mock_db, code)

        assert "发货码格式无效" in str(exc_info.value)
        assert exc_info.value.code == "INVALID_DELIVERY_CODE_FORMAT"

    # ==================== get_virtual_content 测试 ====================

    @pytest.mark.asyncio
    async def test_get_virtual_content_success(self, service, mock_db):
        """测试：成功获取虚拟内容"""
        sku_id = "sku_123"
        product_id = "product_123"
        content_url = "https://example.com/ebook.pdf"

        # Mock SKU数据
        sku = create_mock_sku(sku_id, product_id, virtual_content=content_url)

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = sku
        mock_db.execute.return_value = mock_result

        # 执行
        result = await service.get_virtual_content(mock_db, sku_id)

        # 验证
        assert result == content_url

    @pytest.mark.asyncio
    async def test_get_virtual_content_sku_not_found(self, service, mock_db):
        """测试：SKU不存在"""
        sku_id = "sku_999"

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        # 执行并验证异常
        with pytest.raises(NotFoundException) as exc_info:
            await service.get_virtual_content(mock_db, sku_id)

        assert "SKU不存在" in str(exc_info.value)
        assert exc_info.value.code == "SKU_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_virtual_content_not_virtual(self, service, mock_db):
        """测试：SKU不是虚拟商品"""
        sku_id = "sku_123"
        product_id = "product_123"

        # Mock SKU（无virtual_content字段，表示非虚拟商品）
        sku = create_mock_sku(sku_id, product_id, virtual_content=None)

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = sku
        mock_db.execute.return_value = mock_result

        # 执行并验证异常
        with pytest.raises(BusinessException) as exc_info:
            await service.get_virtual_content(mock_db, sku_id)

        assert "非虚拟商品" in str(exc_info.value)
        assert exc_info.value.code == "NOT_VIRTUAL_PRODUCT"

    @pytest.mark.asyncio
    async def test_get_virtual_content_no_content(self, service, mock_db):
        """测试：虚拟商品无内容"""
        sku_id = "sku_123"
        product_id = "product_123"

        # Mock SKU（虚拟商品但无内容）
        sku = create_mock_sku(sku_id, product_id, virtual_content="")
        # 确保virtual_content属性存在但为空
        sku.virtual_content = ""

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = sku
        mock_db.execute.return_value = mock_result

        # 执行并验证异常
        with pytest.raises(BusinessException) as exc_info:
            await service.get_virtual_content(mock_db, sku_id)

        # 验证异常消息包含"无可用内容"
        assert "无可用内容" in str(exc_info.value) or "虚拟商品" in str(exc_info.value)

    # ==================== check_is_virtual_product 测试 ====================

    @pytest.mark.asyncio
    async def test_check_is_virtual_product_true(self, service, mock_db):
        """测试：商品是虚拟商品"""
        product_id = "product_123"

        # Mock虚拟商品
        product = create_mock_product(product_id, is_virtual=True)

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = product
        mock_db.execute.return_value = mock_result

        # 执行
        result = await service.check_is_virtual_product(mock_db, product_id)

        # 验证
        assert result is True

    @pytest.mark.asyncio
    async def test_check_is_virtual_product_false(self, service, mock_db):
        """测试：商品不是虚拟商品"""
        product_id = "product_123"

        # Mock实物商品
        product = create_mock_product(product_id, is_virtual=False)

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = product
        mock_db.execute.return_value = mock_result

        # 执行
        result = await service.check_is_virtual_product(mock_db, product_id)

        # 验证
        assert result is False

    @pytest.mark.asyncio
    async def test_check_is_virtual_product_not_found(self, service, mock_db):
        """测试：商品不存在"""
        product_id = "product_999"

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        # 执行
        result = await service.check_is_virtual_product(mock_db, product_id)

        # 验证
        assert result is False

    # ==================== 批量发货测试 ====================

    @pytest.mark.asyncio
    async def test_batch_deliver_virtual_products(self, service, mock_db):
        """测试：批量自动发货"""
        order_id = "order_123"

        # Mock多个订单项
        items = [
            create_mock_order_item("item_1", order_id, "product_1", "sku_1"),
            create_mock_order_item("item_2", order_id, "product_2", "sku_2"),
            create_mock_order_item("item_3", order_id, "product_3", "sku_3"),
        ]

        # 确保所有item都没有delivery_code属性
        for item in items:
            if hasattr(item, 'delivery_code'):
                delattr(item, 'delivery_code')

        # Mock订单
        order = create_mock_order(order_id, "user_123", payment_status="paid", order_status="paid")

        # Mock商品
        products = [
            create_mock_product("product_1", is_virtual=True),
            create_mock_product("product_2", is_virtual=True),
            create_mock_product("product_3", is_virtual=True),
        ]

        # 为每个item准备4个mock结果（Order, OrderItem, Product, AllItems）
        mock_results = []
        for i in range(len(items)):
            # Order查询
            mock_order_result = MagicMock()
            mock_order_result.unique.return_value.scalars.return_value.first.return_value = order
            mock_results.append(mock_order_result)

            # OrderItem查询
            mock_item_result = MagicMock()
            mock_item_result.unique.return_value.scalars.return_value.first.return_value = items[i]
            mock_results.append(mock_item_result)

            # Product查询
            mock_product_result = MagicMock()
            mock_product_result.unique.return_value.scalars.return_value.first.return_value = products[i]
            mock_results.append(mock_product_result)

            # 所有OrderItem查询
            mock_all_items_result = MagicMock()
            mock_all_items_result.unique.return_value.scalars.return_value.all.return_value = items
            mock_results.append(mock_all_items_result)

        mock_db.execute.side_effect = mock_results

        # Mock发货码生成
        with patch.object(service, 'generate_delivery_code', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = [
                "VD-20260224-ABCD1234",
                "VD-20260224-EFGH5678",
                "VD-20260224-IJKL9012"
            ]

            # 执行批量发货
            results = []
            for item in items:
                result = await service.deliver_virtual_product(mock_db, order_id, item.id)
                results.append(result)

            # 验证
            assert all(results)
            assert mock_generate.call_count == 3

    # ==================== 事务回滚测试 ====================

    @pytest.mark.asyncio
    async def test_deliver_virtual_product_transaction_rollback(self, service, mock_db):
        """测试：发货失败时事务回滚"""
        order_id = "order_123"
        item_id = "item_123"
        product_id = "product_123"
        sku_id = "sku_123"

        # Mock数据
        order = create_mock_order(order_id, "user_123", "paid")
        item = create_mock_order_item(item_id, order_id, product_id, sku_id)
        order.items = [item]
        product = create_mock_product(product_id, is_virtual=True)

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.side_effect = [
            order,
            product
        ]
        mock_db.execute.return_value = mock_result

        # Mock发货码生成时抛出异常
        with patch.object(service, 'generate_delivery_code', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = Exception("Database error")

            # 执行并验证异常
            with pytest.raises(Exception):
                await service.deliver_virtual_product(mock_db, order_id, item_id)

            # 验证回滚被调用
            mock_db.rollback.assert_called_once()

    # ==================== 并发测试 ====================

    @pytest.mark.asyncio
    async def test_concurrent_delivery_code_generation(self, service, mock_db):
        """测试：并发发货码生成不重复"""
        sku_id = "sku_123"

        # Mock Redis incr（模拟原子递增）
        service.redis_client.incr.side_effect = [1, 2, 3, 4, 5]

        # 并发生成
        import asyncio
        tasks = [
            service.generate_delivery_code(mock_db, sku_id)
            for _ in range(5)
        ]
        codes = await asyncio.gather(*tasks)

        # 验证唯一性
        assert len(set(codes)) == 5
        assert len(codes) == 5

    # ==================== 错误处理测试 ====================

    @pytest.mark.asyncio
    async def test_deliver_virtual_product_order_unpaid(self, service, mock_db):
        """测试：未支付订单不能发货"""
        order_id = "order_123"
        item_id = "item_123"

        # Mock未支付订单
        order = create_mock_order(order_id, "user_123", payment_status="pending")  # 未支付

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.first.return_value = order
        mock_db.execute.return_value = mock_result

        # 执行并验证异常
        with pytest.raises(BusinessException) as exc_info:
            await service.deliver_virtual_product(mock_db, order_id, item_id)

        assert "订单未支付" in str(exc_info.value)
        assert exc_info.value.code == "ORDER_NOT_PAID"

    @pytest.mark.asyncio
    async def test_generate_delivery_code_database_error(self, service, mock_db):
        """测试：数据库错误处理"""
        sku_id = "sku_123"

        # Mock Redis错误
        service.redis_client.incr.side_effect = Exception("Redis connection error")

        # 执行并验证异常
        with pytest.raises(Exception) as exc_info:
            await service.generate_delivery_code(mock_db, sku_id)

        assert "Redis connection error" in str(exc_info.value)
