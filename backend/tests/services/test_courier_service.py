"""
单元测试 - 物流公司服务 (app.services.courier_service)
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.courier_service import (
    create_courier,
    get_courier,
    list_couriers,
    get_courier_by_code,
    update_courier,
    delete_courier,
)
from app.core.exceptions import NotFoundException, ValidationException


@pytest.mark.asyncio
async def test_create_courier(db_session: AsyncSession):
    """Test creating a courier company"""
    courier = await create_courier(
        db_session,
        name="顺丰速运",
        code="SF",
        website="https://www.sf-express.com",
        tracking_url="https://www.sf-express.com/trace",
        supports_cod=True,
        supports_cold_chain=True,
        sort_order=1
    )

    assert courier.id is not None
    assert courier.name == "顺丰速运"
    assert courier.code == "SF"  # Should be uppercase automatically
    assert courier.website == "https://www.sf-express.com"
    assert courier.tracking_url == "https://www.sf-express.com/trace"
    assert courier.supports_cod is True
    assert courier.supports_cold_chain is True
    assert courier.sort_order == 1
    assert courier.is_active is True


@pytest.mark.asyncio
async def test_create_courier_code_to_uppercase(db_session: AsyncSession):
    """Test that courier code is automatically converted to uppercase"""
    courier = await create_courier(
        db_session,
        name="中通快递",
        code="zt"  # Lowercase input
    )

    assert courier.code == "ZT"  # Should be uppercase


@pytest.mark.asyncio
async def test_create_courier_duplicate_code(db_session: AsyncSession):
    """Test creating a courier with duplicate code should fail"""
    await create_courier(
        db_session,
        name="顺丰速运",
        code="SF"
    )

    # Try to create another courier with the same code
    with pytest.raises(ValidationException):
        await create_courier(
            db_session,
            name="顺丰速运2",
            code="SF"
        )


@pytest.mark.asyncio
async def test_get_courier(db_session: AsyncSession):
    """Test getting a courier by ID"""
    courier = await create_courier(
        db_session,
        name="京东物流",
        code="JD"
    )

    fetched = await get_courier(db_session, courier.id)

    assert fetched.id == courier.id
    assert fetched.name == "京东物流"
    assert fetched.code == "JD"


@pytest.mark.asyncio
async def test_get_courier_not_found(db_session: AsyncSession):
    """Test getting a non-existent courier"""
    with pytest.raises(NotFoundException):
        await get_courier(db_session, "nonexistent-id")


@pytest.mark.asyncio
async def test_get_courier_by_code(db_session: AsyncSession):
    """Test getting a courier by code"""
    await create_courier(
        db_session,
        name="圆通速递",
        code="YTO"
    )

    courier = await get_courier_by_code(db_session, "YTO")

    assert courier is not None
    assert courier.name == "圆通速递"
    assert courier.code == "YTO"


@pytest.mark.asyncio
async def test_get_courier_by_code_not_found(db_session: AsyncSession):
    """Test getting a courier by non-existent code"""
    courier = await get_courier_by_code(db_session, "NONEXISTENT")

    assert courier is None


@pytest.mark.asyncio
async def test_get_courier_by_code_case_insensitive(db_session: AsyncSession):
    """Test that get_courier_by_code is case-insensitive"""
    await create_courier(
        db_session,
        name="韵达速递",
        code="YD"
    )

    # Search with lowercase
    courier = await get_courier_by_code(db_session, "yd")

    assert courier is not None
    assert courier.code == "YD"


@pytest.mark.asyncio
async def test_list_couriers(db_session: AsyncSession):
    """Test listing all couriers"""
    await create_courier(db_session, name="顺丰", code="SF", sort_order=2)
    await create_courier(db_session, name="中通", code="ZTO", sort_order=1)
    await create_courier(db_session, name="圆通", code="YTO", sort_order=3)

    couriers = await list_couriers(db_session)

    assert len(couriers) == 3
    # Should be sorted by sort_order
    assert couriers[0].name == "中通"
    assert couriers[1].name == "顺丰"
    assert couriers[2].name == "圆通"


@pytest.mark.asyncio
async def test_list_couriers_active_only(db_session: AsyncSession):
    """Test listing only active couriers"""
    await create_courier(db_session, name="启用", code="ON", is_active=True)
    await create_courier(db_session, name="禁用", code="OFF", is_active=False)

    couriers = await list_couriers(db_session, active_only=True)

    assert len(couriers) == 1
    assert couriers[0].name == "启用"


@pytest.mark.asyncio
async def test_list_couriers_empty(db_session: AsyncSession):
    """Test listing couriers when none exist"""
    couriers = await list_couriers(db_session)

    assert len(couriers) == 0


@pytest.mark.asyncio
async def test_update_courier(db_session: AsyncSession):
    """Test updating a courier"""
    courier = await create_courier(
        db_session,
        name="旧名称",
        code="OLD"
    )

    updated = await update_courier(
        db_session,
        courier.id,
        name="新名称",
        website="https://new.com",
        supports_cod=True
    )

    assert updated.name == "新名称"
    assert updated.website == "https://new.com"
    assert updated.supports_cod is True
    assert updated.code == "OLD"  # Code should not change


@pytest.mark.asyncio
async def test_update_courier_not_found(db_session: AsyncSession):
    """Test updating a non-existent courier"""
    with pytest.raises(NotFoundException):
        await update_courier(
            db_session,
            "nonexistent-id",
            name="新名称"
        )


@pytest.mark.asyncio
async def test_delete_courier(db_session: AsyncSession):
    """Test deleting a courier"""
    courier = await create_courier(
        db_session,
        name="待删除",
        code="DEL"
    )

    await delete_courier(db_session, courier.id)

    # Verify courier is deleted
    with pytest.raises(NotFoundException):
        await get_courier(db_session, courier.id)


@pytest.mark.asyncio
async def test_delete_courier_not_found(db_session: AsyncSession):
    """Test deleting a non-existent courier"""
    with pytest.raises(NotFoundException):
        await delete_courier(db_session, "nonexistent-id")
