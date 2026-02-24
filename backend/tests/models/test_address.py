import pytest
from app.models.address import AdminRegion, UserAddress


@pytest.mark.asyncio
async def test_create_admin_region(db_session):
    """Test creating an administrative region"""
    region = AdminRegion(
        code="110000",
        name="北京市",
        level="province",
        sort_order=1
    )
    db_session.add(region)
    await db_session.commit()
    await db_session.refresh(region)

    assert region.name == "北京市"
    assert region.level == "province"
    assert region.code == "110000"


@pytest.mark.asyncio
async def test_region_hierarchy(db_session):
    """Test region parent-child relationship"""
    # Province
    province = AdminRegion(
        code="440000",
        name="广东省",
        level="province"
    )
    db_session.add(province)
    await db_session.flush()

    # City
    city = AdminRegion(
        code="440300",
        name="深圳市",
        level="city",
        parent_code="440000"
    )
    db_session.add(city)
    await db_session.flush()

    # District
    district = AdminRegion(
        code="440305",
        name="南山区",
        level="district",
        parent_code="440300"
    )
    db_session.add(district)
    await db_session.commit()

    assert city.parent_code == province.code
    assert district.parent_code == city.code
    assert province.level == "province"
    assert city.level == "city"
    assert district.level == "district"


@pytest.mark.asyncio
async def test_create_user_address(db_session):
    """Test creating a user delivery address"""
    address = UserAddress(
        user_id="user-123",
        province_code="440000",
        province_name="广东省",
        city_code="440300",
        city_name="深圳市",
        district_code="440305",
        district_name="南山区",
        detailed_address="科技园南区深圳湾科技生态园",
        postal_code="518057",
        contact_name="张三",
        contact_phone="13800138000",
        is_default=True
    )
    db_session.add(address)
    await db_session.commit()
    await db_session.refresh(address)

    assert address.province_name == "广东省"
    assert address.city_name == "深圳市"
    assert address.district_name == "南山区"
    assert address.detailed_address == "科技园南区深圳湾科技生态园"
    assert address.contact_name == "张三"
    assert address.contact_phone == "13800138000"
    assert address.is_default is True
