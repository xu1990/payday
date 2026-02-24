import pytest
from app.models.product import ProductCategory, Product


@pytest.mark.asyncio
async def test_create_category(db_session):
    """Test creating a product category"""
    category = ProductCategory(
        id="cat-1",
        name="数码产品",
        code="digital",
        sort_order=1
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    assert category.name == "数码产品"
    assert category.code == "digital"


@pytest.mark.asyncio
async def test_category_hierarchy(db_session):
    """Test category parent-child relationship"""
    # Parent category
    parent = ProductCategory(
        id="cat-parent",
        name="电子产品",
        code="electronics"
    )
    db_session.add(parent)
    await db_session.flush()

    # Child category
    child = ProductCategory(
        id="cat-child",
        name="手机",
        code="phone",
        parent_id="cat-parent"
    )
    db_session.add(child)
    await db_session.commit()

    assert child.parent_id == parent.id


@pytest.mark.asyncio
async def test_create_product_with_sku(db_session):
    """Test creating product with SKU variants"""
    # Create product
    product = Product(
        id="prod-1",
        name="T恤",
        item_type="physical",
        product_type="cash"
    )
    db_session.add(product)
    await db_session.flush()

    # Create SKU
    from app.models.product import ProductSKU

    sku = ProductSKU(
        id="sku-1",
        product_id="prod-1",
        sku_code="TSHIRT-RED-L",
        name="红色 - L码",
        attributes={"color": "red", "size": "L"},
        stock=100,
        weight_grams=200
    )
    db_session.add(sku)
    await db_session.commit()

    assert sku.attributes["color"] == "red"
    assert sku.stock == 100
