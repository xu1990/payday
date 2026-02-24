import pytest
from app.models.shipping import ShippingTemplate, ShippingTemplateRegion, CourierCompany


@pytest.mark.asyncio
async def test_create_shipping_template(db_session):
    """Test creating a shipping template"""
    template = ShippingTemplate(
        name="全国包邮",
        description="订单满99元包邮",
        charge_type="weight",
        default_first_unit=1000,
        default_first_cost=1000,
        default_continue_unit=1000,
        default_continue_cost=500,
        free_threshold=9900,
        estimate_days_min=3,
        estimate_days_max=7
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    assert template.name == "全国包邮"
    assert template.charge_type == "weight"
    assert template.free_threshold == 9900
    assert template.estimate_days_min == 3
    assert template.estimate_days_max == 7


@pytest.mark.asyncio
async def test_shipping_template_region(db_session):
    """Test creating shipping template with regional pricing"""
    # Create template
    template = ShippingTemplate(
        name="差异化运费",
        charge_type="quantity",
        default_first_unit=1,
        default_first_cost=1000,
        default_continue_unit=1,
        default_continue_cost=200
    )
    db_session.add(template)
    await db_session.flush()

    # Add regional pricing for remote areas
    region = ShippingTemplateRegion(
        template_id=template.id,
        region_codes="650000,659001",
        region_names="新疆,新疆维吾尔自治区",
        first_unit=1,
        first_cost=2000,
        continue_unit=1,
        continue_cost=500,
        free_threshold=19900
    )
    db_session.add(region)
    await db_session.commit()
    await db_session.refresh(region)

    assert region.region_codes == "650000,659001"
    assert region.region_names == "新疆,新疆维吾尔自治区"
    assert region.first_cost == 2000
    assert region.free_threshold == 19900


@pytest.mark.asyncio
async def test_courier_company(db_session):
    """Test creating a courier company"""
    courier = CourierCompany(
        code="SF_EXPRESS",
        name="顺丰速运",
        website="https://www.sf-express.com",
        tracking_url="https://www.sf-express.com/trace",
        supports_cod=False,
        supports_cold_chain=True,
        sort_order=1
    )
    db_session.add(courier)
    await db_session.commit()
    await db_session.refresh(courier)

    assert courier.code == "SF_EXPRESS"
    assert courier.name == "顺丰速运"
    assert courier.supports_cod is False
    assert courier.supports_cold_chain is True
