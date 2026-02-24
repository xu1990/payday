import pytest
from app.models.product import ProductCategory


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
