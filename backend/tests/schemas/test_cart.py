"""
单元测试 - 购物车模式 (app.schemas.cart)
"""
import pytest
from pydantic import ValidationError


class TestProductBasicInfo:
    """测试商品基础信息模式"""

    def test_product_basic_info(self):
        """测试商品基础信息"""
        from app.schemas.cart import ProductBasicInfo

        product = ProductBasicInfo(
            id="product_123",
            name="测试商品",
            description="这是一个测试商品",
            images=["image1.jpg", "image2.jpg"],
            product_type="point",
            item_type="physical",
            is_active=True
        )
        assert product.id == "product_123"
        assert product.name == "测试商品"
        assert len(product.images) == 2


class TestSKUBasicInfo:
    """测试SKU基础信息模式"""

    def test_sku_basic_info(self):
        """测试SKU基础信息"""
        from app.schemas.cart import SKUBasicInfo

        sku = SKUBasicInfo(
            id="sku_123",
            sku_code="SKU001",
            name="红色-L码",
            attributes={"color": "红色", "size": "L"},
            stock=100,
            price=99.99,
            currency="CNY"
        )
        assert sku.id == "sku_123"
        assert sku.attributes == {"color": "红色", "size": "L"}


class TestCartItemCreate:
    """测试购物车项创建模式"""

    def test_valid_cart_item_create(self):
        """测试有效的购物车项创建"""
        from app.schemas.cart import CartItemCreate

        item = CartItemCreate(
            sku_id="sku_123",
            quantity=2
        )
        assert item.sku_id == "sku_123"
        assert item.quantity == 2

    def test_quantity_must_be_positive(self):
        """测试数量必须大于等于1"""
        from app.schemas.cart import CartItemCreate

        with pytest.raises(ValidationError) as exc_info:
            CartItemCreate(sku_id="sku_123", quantity=0)
        assert "quantity" in str(exc_info.value).lower()

    def test_quantity_cannot_be_negative(self):
        """测试数量不能为负数"""
        from app.schemas.cart import CartItemCreate

        with pytest.raises(ValidationError) as exc_info:
            CartItemCreate(sku_id="sku_123", quantity=-1)
        assert "quantity" in str(exc_info.value).lower()


class TestCartItemUpdate:
    """测试购物车项更新模式"""

    def test_valid_quantity_update(self):
        """测试有效的数量更新"""
        from app.schemas.cart import CartItemUpdate

        update = CartItemUpdate(quantity=5)
        assert update.quantity == 5

    def test_quantity_update_must_be_positive(self):
        """测试更新数量必须大于等于1"""
        from app.schemas.cart import CartItemUpdate

        with pytest.raises(ValidationError) as exc_info:
            CartItemUpdate(quantity=0)
        assert "quantity" in str(exc_info.value).lower()


class TestCartItemResponse:
    """测试购物车项响应模式"""

    def test_cart_item_response_fields(self):
        """测试购物车项响应字段"""
        from app.schemas.cart import CartItemResponse, ProductBasicInfo, SKUBasicInfo

        product = ProductBasicInfo(
            id="product_123",
            name="测试商品",
            description="商品描述",
            images=["image.jpg"],
            product_type="cash",
            item_type="physical",
            is_active=True
        )

        sku = SKUBasicInfo(
            id="sku_123",
            sku_code="SKU001",
            name="红色-L码",
            attributes={"color": "red", "size": "L"},
            stock=50,
            price=99.99,
            currency="CNY"
        )

        item = CartItemResponse(
            id="cart_item_123",
            sku_id="sku_123",
            quantity=2,
            product=product,
            sku=sku
        )
        assert item.id == "cart_item_123"
        assert item.quantity == 2
        assert item.product.name == "测试商品"
        assert item.sku.attributes == {"color": "red", "size": "L"}

    def test_json_serialization(self):
        """测试JSON序列化"""
        from app.schemas.cart import CartItemResponse, ProductBasicInfo, SKUBasicInfo

        product = ProductBasicInfo(
            id="product_123",
            name="测试商品",
            description=None,
            images=None,
            product_type="point",
            item_type="virtual",
            is_active=True
        )

        sku = SKUBasicInfo(
            id="sku_123",
            sku_code="SKU001",
            name="虚拟商品",
            attributes={},
            stock=999,
            price=100,
            currency="POINTS"
        )

        item = CartItemResponse(
            id="cart_item_123",
            sku_id="sku_123",
            quantity=1,
            product=product,
            sku=sku
        )
        json_data = item.model_dump_json()
        assert "cart_item_123" in json_data
        assert "测试商品" in json_data


class TestCartResponse:
    """测试购物车响应模式"""

    def test_cart_response_fields(self):
        """测试购物车响应字段"""
        from app.schemas.cart import CartResponse

        cart = CartResponse(
            items=[],
            total_amount=29999,
            total_points=1000,
            item_count=3
        )
        assert cart.items == []
        assert cart.total_amount == 29999
        assert cart.total_points == 1000
        assert cart.item_count == 3

    def test_cart_with_items(self):
        """测试带商品的购物车"""
        from app.schemas.cart import CartResponse, CartItemResponse, ProductBasicInfo, SKUBasicInfo

        product = ProductBasicInfo(
            id="product_123",
            name="测试商品",
            description="描述",
            images=["image.jpg"],
            product_type="hybrid",
            item_type="physical",
            is_active=True
        )

        sku = SKUBasicInfo(
            id="sku_123",
            sku_code="SKU001",
            name="标准版",
            attributes={"version": "standard"},
            stock=10,
            price=199.99,
            currency="CNY"
        )

        item = CartItemResponse(
            id="cart_item_123",
            sku_id="sku_123",
            quantity=2,
            product=product,
            sku=sku
        )

        cart = CartResponse(
            items=[item],
            total_amount=39998,
            total_points=0,
            item_count=2
        )
        assert len(cart.items) == 1
        assert cart.items[0].product.name == "测试商品"
        assert cart.item_count == 2

    def test_empty_cart(self):
        """测试空购物车"""
        from app.schemas.cart import CartResponse

        cart = CartResponse(
            items=[],
            total_amount=0,
            total_points=0,
            item_count=0
        )
        assert cart.item_count == 0
        assert cart.total_amount == 0
        assert cart.total_points == 0

    def test_json_serialization(self):
        """测试JSON序列化"""
        from app.schemas.cart import CartResponse

        cart = CartResponse(
            items=[],
            total_amount=10000,
            total_points=500,
            item_count=1
        )
        json_data = cart.model_dump_json()
        assert "10000" in json_data
        assert "500" in json_data
