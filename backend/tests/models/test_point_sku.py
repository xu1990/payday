import pytest
import json
from app.models.point_sku import PointSpecification, PointSpecificationValue, PointProductSKU
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_specification(db_session: AsyncSession):
    """Test creating a product specification"""
    spec = PointSpecification(
        product_id="test-product-id",
        name="颜色",
        sort_order=0
    )
    db_session.add(spec)
    await db_session.flush()

    assert spec.id is not None
    assert spec.name == "颜色"


@pytest.mark.asyncio
async def test_create_specification_value(db_session: AsyncSession):
    """Test creating specification values"""
    spec = PointSpecification(
        product_id="test-product-id",
        name="颜色"
    )
    db_session.add(spec)
    await db_session.flush()

    value = PointSpecificationValue(
        specification_id=spec.id,
        value="红色",
        sort_order=0
    )
    db_session.add(value)
    await db_session.flush()

    assert value.specification_id == spec.id
    assert value.value == "红色"


@pytest.mark.asyncio
async def test_create_sku(db_session: AsyncSession):
    """Test creating a product SKU"""
    sku = PointProductSKU(
        product_id="test-product-id",
        sku_code="PROD-RED-L",
        specs=json.dumps({"颜色": "红色", "尺寸": "L"}),
        stock=10,
        stock_unlimited=False,
        points_cost=100,
        is_active=True
    )
    db_session.add(sku)
    await db_session.flush()

    assert sku.id is not None
    assert sku.sku_code == "PROD-RED-L"
    assert json.loads(sku.specs) == {"颜色": "红色", "尺寸": "L"}
