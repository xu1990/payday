import pytest
from app.models.point_return import PointReturn
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_return_request(db_session: AsyncSession):
    """Test creating a return request"""
    return_request = PointReturn(
        order_id="test-order-id",
        reason="商品质量问题",
        status="requested"
    )
    db_session.add(return_request)
    await db_session.flush()

    assert return_request.id is not None
    assert return_request.status == "requested"
    assert return_request.reason == "商品质量问题"


@pytest.mark.asyncio
async def test_approve_return(db_session: AsyncSession):
    """Test approving a return"""
    return_request = PointReturn(
        order_id="test-order-id",
        reason="不想要了",
        status="requested"
    )
    db_session.add(return_request)
    await db_session.flush()

    return_request.status = "approved"
    return_request.admin_notes = "同意退款"
    return_request.admin_id = "test-admin-id"

    await db_session.flush()

    assert return_request.status == "approved"
    assert return_request.admin_notes == "同意退款"
