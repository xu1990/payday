"""
单元测试 - 积分退货服务 (app.services.point_return_service)
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.point_return_service import (
    create_return,
    list_returns,
    get_return,
    approve_return,
    reject_return,
)
from app.core.exceptions import NotFoundException, BusinessException, ValidationException


@pytest.mark.asyncio
async def test_create_return(db_session: AsyncSession):
    """Test creating a return request"""
    from app.models.point_return import PointReturn
    from app.models.point_order import PointOrder
    from app.models.point_product import PointProduct
    from tests.test_utils import TestDataFactory
    from app.utils.order_number import generate_order_number

    # Create test data
    user = await TestDataFactory.create_user(db_session, openid="test_openid")

    product = PointProduct(
        name="测试商品",
        points_cost=100,
        stock=10,
        stock_unlimited=False,
        description="测试商品描述",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    order = PointOrder(
        user_id=user.id,
        product_id=product.id,
        order_number=generate_order_number(),
        product_name=product.name,
        points_cost=product.points_cost,
        status="pending",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create return request
    return_request = await create_return(
        db_session,
        order.id,
        "不喜欢这个商品",
    )

    assert return_request.id is not None
    assert return_request.order_id == order.id
    assert return_request.reason == "不喜欢这个商品"
    assert return_request.status == "requested"
    assert return_request.admin_id is None
    assert return_request.admin_notes is None
    assert return_request.created_at is not None
    assert return_request.processed_at is None


@pytest.mark.asyncio
async def test_create_return_not_found(db_session: AsyncSession):
    """Test creating a return request for non-existent order"""
    with pytest.raises(NotFoundException):
        await create_return(
            db_session,
            "nonexistent-order-id",
            "测试原因",
        )


@pytest.mark.asyncio
async def test_list_returns_empty(db_session: AsyncSession):
    """Test listing returns when no returns exist"""
    returns = await list_returns(db_session)
    assert len(returns) == 0


@pytest.mark.asyncio
async def test_list_returns_with_data(db_session: AsyncSession):
    """Test listing returns with data"""
    from app.models.point_return import PointReturn
    from app.models.point_order import PointOrder
    from app.models.point_product import PointProduct
    from tests.test_utils import TestDataFactory
    from app.utils.order_number import generate_order_number

    # Create test data
    user = await TestDataFactory.create_user(db_session, openid="test_openid")

    product = PointProduct(
        name="测试商品",
        points_cost=100,
        stock=10,
        stock_unlimited=False,
        description="测试商品描述",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Create two separate orders
    order1 = PointOrder(
        user_id=user.id,
        product_id=product.id,
        order_number=generate_order_number(),
        product_name=product.name,
        points_cost=product.points_cost,
        status="pending",
    )
    db_session.add(order1)
    await db_session.commit()
    await db_session.refresh(order1)

    order2 = PointOrder(
        user_id=user.id,
        product_id=product.id,
        order_number=generate_order_number(),
        product_name=product.name,
        points_cost=product.points_cost,
        status="pending",
    )
    db_session.add(order2)
    await db_session.commit()
    await db_session.refresh(order2)

    # Create return requests for different orders
    await create_return(db_session, order1.id, "原因1")
    await create_return(db_session, order2.id, "原因2")

    # List returns
    returns = await list_returns(db_session)
    assert len(returns) == 2
    assert all(r.status == "requested" for r in returns)


@pytest.mark.asyncio
async def test_list_returns_by_status(db_session: AsyncSession):
    """Test listing returns by status"""
    from app.models.point_return import PointReturn
    from app.models.point_order import PointOrder
    from app.models.point_product import PointProduct
    from tests.test_utils import TestDataFactory
    from app.utils.order_number import generate_order_number

    # Create test data
    user = await TestDataFactory.create_user(db_session, openid="test_openid")

    product = PointProduct(
        name="测试商品",
        points_cost=100,
        stock=10,
        stock_unlimited=False,
        description="测试商品描述",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Create two separate orders
    order1 = PointOrder(
        user_id=user.id,
        product_id=product.id,
        order_number=generate_order_number(),
        product_name=product.name,
        points_cost=product.points_cost,
        status="pending",
    )
    db_session.add(order1)
    await db_session.commit()
    await db_session.refresh(order1)

    order2 = PointOrder(
        user_id=user.id,
        product_id=product.id,
        order_number=generate_order_number(),
        product_name=product.name,
        points_cost=product.points_cost,
        status="pending",
    )
    db_session.add(order2)
    await db_session.commit()
    await db_session.refresh(order2)

    # Create return requests for different orders
    return1 = await create_return(db_session, order1.id, "原因1")
    return2 = await create_return(db_session, order2.id, "原因2")

    # Update one return to approved
    return1.status = "approved"
    await db_session.commit()

    # Test listing by status
    requested_returns = await list_returns(db_session, status="requested")
    approved_returns = await list_returns(db_session, status="approved")

    assert len(requested_returns) == 1
    assert len(approved_returns) == 1
    assert requested_returns[0].status == "requested"
    assert approved_returns[0].status == "approved"


@pytest.mark.asyncio
async def test_get_return(db_session: AsyncSession):
    """Test getting a return by ID"""
    from app.models.point_return import PointReturn
    from app.models.point_order import PointOrder
    from app.models.point_product import PointProduct
    from tests.test_utils import TestDataFactory
    from app.utils.order_number import generate_order_number

    # Create test data
    user = await TestDataFactory.create_user(db_session, openid="test_openid")

    product = PointProduct(
        name="测试商品",
        points_cost=100,
        stock=10,
        stock_unlimited=False,
        description="测试商品描述",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    order = PointOrder(
        user_id=user.id,
        product_id=product.id,
        order_number=generate_order_number(),
        product_name=product.name,
        points_cost=product.points_cost,
        status="pending",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create return request
    return_request = await create_return(db_session, order.id, "测试原因")

    # Get return by ID
    fetched = await get_return(db_session, return_request.id)

    assert fetched.id == return_request.id
    assert fetched.reason == "测试原因"


@pytest.mark.asyncio
async def test_get_return_not_found(db_session: AsyncSession):
    """Test getting a non-existent return"""
    with pytest.raises(NotFoundException):
        await get_return(db_session, "nonexistent-return-id")


@pytest.mark.asyncio
async def test_approve_return(db_session: AsyncSession):
    """Test approving a return request"""
    from app.models.point_return import PointReturn
    from app.models.point_order import PointOrder
    from app.models.point_product import PointProduct
    from tests.test_utils import TestDataFactory
    from app.utils.order_number import generate_order_number

    # Create test data
    user = await TestDataFactory.create_user(db_session, openid="test_openid")

    product = PointProduct(
        name="测试商品",
        points_cost=100,
        stock=10,
        stock_unlimited=False,
        description="测试商品描述",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    order = PointOrder(
        user_id=user.id,
        product_id=product.id,
        order_number=generate_order_number(),
        product_name=product.name,
        points_cost=product.points_cost,
        status="pending",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create return request
    return_request = await create_return(db_session, order.id, "测试原因")

    # Approve return
    admin_id = "test_admin_id"
    approved = await approve_return(
        db_session,
        return_request.id,
        admin_id,
        "同意退货"
    )

    assert approved.status == "approved"
    assert approved.admin_id == admin_id
    assert approved.admin_notes == "同意退货"
    assert approved.processed_at is not None


@pytest.mark.asyncio
async def test_approve_return_not_found(db_session: AsyncSession):
    """Test approving a non-existent return"""
    with pytest.raises(NotFoundException):
        await approve_return(
            db_session,
            "nonexistent-return-id",
            "test_admin_id",
            "测试备注"
        )


@pytest.mark.asyncio
async def test_approve_return_already_processed(db_session: AsyncSession):
    """Test approving a return that's already processed"""
    from app.models.point_return import PointReturn
    from app.models.point_order import PointOrder
    from app.models.point_product import PointProduct
    from tests.test_utils import TestDataFactory
    from app.utils.order_number import generate_order_number

    # Create test data
    user = await TestDataFactory.create_user(db_session, openid="test_openid")

    product = PointProduct(
        name="测试商品",
        points_cost=100,
        stock=10,
        stock_unlimited=False,
        description="测试商品描述",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    order = PointOrder(
        user_id=user.id,
        product_id=product.id,
        order_number=generate_order_number(),
        product_name=product.name,
        points_cost=product.points_cost,
        status="pending",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create and reject return
    return_request = await create_return(db_session, order.id, "测试原因")
    await reject_return(
        db_session,
        return_request.id,
        "test_admin_id",
        "拒绝退货"
    )

    # Try to approve rejected return
    with pytest.raises(BusinessException):
        await approve_return(
            db_session,
            return_request.id,
            "test_admin_id",
            "备注"
        )


@pytest.mark.asyncio
async def test_reject_return(db_session: AsyncSession):
    """Test rejecting a return request"""
    from app.models.point_return import PointReturn
    from app.models.point_order import PointOrder
    from app.models.point_product import PointProduct
    from tests.test_utils import TestDataFactory
    from app.utils.order_number import generate_order_number

    # Create test data
    user = await TestDataFactory.create_user(db_session, openid="test_openid")

    product = PointProduct(
        name="测试商品",
        points_cost=100,
        stock=10,
        stock_unlimited=False,
        description="测试商品描述",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    order = PointOrder(
        user_id=user.id,
        product_id=product.id,
        order_number=generate_order_number(),
        product_name=product.name,
        points_cost=product.points_cost,
        status="pending",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create return request
    return_request = await create_return(db_session, order.id, "测试原因")

    # Reject return
    admin_id = "test_admin_id"
    rejected = await reject_return(
        db_session,
        return_request.id,
        admin_id,
        "拒绝退货"
    )

    assert rejected.status == "rejected"
    assert rejected.admin_id == admin_id
    assert rejected.admin_notes == "拒绝退货"
    assert rejected.processed_at is not None


@pytest.mark.asyncio
async def test_reject_return_not_found(db_session: AsyncSession):
    """Test rejecting a non-existent return"""
    with pytest.raises(NotFoundException):
        await reject_return(
            db_session,
            "nonexistent-return-id",
            "test_admin_id",
            "测试备注"
        )


@pytest.mark.asyncio
async def test_reject_return_already_processed(db_session: AsyncSession):
    """Test rejecting a return that's already processed"""
    from app.models.point_return import PointReturn
    from app.models.point_order import PointOrder
    from app.models.point_product import PointProduct
    from tests.test_utils import TestDataFactory
    from app.utils.order_number import generate_order_number

    # Create test data
    user = await TestDataFactory.create_user(db_session, openid="test_openid")

    product = PointProduct(
        name="测试商品",
        points_cost=100,
        stock=10,
        stock_unlimited=False,
        description="测试商品描述",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    order = PointOrder(
        user_id=user.id,
        product_id=product.id,
        order_number=generate_order_number(),
        product_name=product.name,
        points_cost=product.points_cost,
        status="pending",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create and approve return
    return_request = await create_return(db_session, order.id, "测试原因")
    await approve_return(
        db_session,
        return_request.id,
        "test_admin_id",
        "同意退货"
    )

    # Try to reject approved return
    with pytest.raises(BusinessException):
        await reject_return(
            db_session,
            return_request.id,
            "test_admin_id",
            "备注"
        )