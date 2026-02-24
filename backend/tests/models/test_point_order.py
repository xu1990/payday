"""Test PointOrder model - Sprint 4.7"""
import pytest
from app.models.point_order import PointOrder
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_order_with_sku_and_address(db_session: AsyncSession):
    """Test order with SKU and address references"""
    order = PointOrder(
        user_id="test-user-id",
        product_id="test-product-id",
        order_number="PO20250101001",
        product_name="测试商品",
        points_cost=100,
        sku_id="test-sku-id",
        address_id="test-address-id",
        shipment_id="test-shipment-id"
    )
    db_session.add(order)
    await db_session.flush()

    assert order.sku_id == "test-sku-id"
    assert order.address_id == "test-address-id"
    assert order.shipment_id == "test-shipment-id"
