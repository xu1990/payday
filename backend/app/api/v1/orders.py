"""
订单接口 - Sprint 3.8 电商订单系统
Order API Endpoints

提供订单相关的所有API端点：
- POST /orders - 创建订单
- GET /orders - 获取订单列表（分页）
- GET /orders/{order_id} - 获取订单详情
- PUT /orders/{order_id}/cancel - 取消订单
- GET /orders/{order_id}/status - 获取订单状态

关键特性：
- 使用OrderService处理业务逻辑
- JWT认证保护所有端点
- 订单所有权验证
- 支持状态筛选和分页
- 统一错误处理
"""
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import (
    success_response,
    NotFoundException,
    BusinessException,
)
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


class CancelOrderRequest(BaseModel):
    """取消订单请求"""
    reason: Optional[str] = None


@router.post(
    "",
    response_model=Dict[str, Any],
    summary="创建订单",
    description="从购物车商品创建订单，支持积分、现金、混合支付"
)
async def create_order_endpoint(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    创建订单

    从购物车商品创建订单，流程：
    1. 验证SKU库存并锁定
    2. 计算订单金额
    3. 验证积分余额
    4. 创建订单和订单明细
    5. 返回订单信息

    Args:
        order_data: 订单创建数据（商品列表、收货地址、支付方式等）
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 创建的订单信息

    Raises:
        ValidationException: 请求数据验证失败
        NotFoundException: SKU、商品或收货地址不存在
        BusinessException: 库存不足、积分不足等业务错误
    """
    try:
        # 初始化订单服务
        order_service = OrderService()

        # 创建订单
        order = await order_service.create_order(
            db=db,
            user_id=str(current_user.id),
            order_data=order_data
        )

        # 返回成功响应
        return success_response(
            data=order.model_dump(),
            message="订单创建成功"
        )

    except (NotFoundException, BusinessException) as e:
        # 业务异常直接抛出
        raise e

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating order for user {current_user.id}: {e}")

        # 返回友好错误信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建订单失败，请稍后重试"
        )


@router.get(
    "",
    response_model=Dict[str, Any],
    summary="获取订单列表",
    description="获取当前用户的订单列表，支持分页和状态筛选"
)
async def list_orders_endpoint(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="状态筛选（pending/paid/completed等）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取订单列表

    返回当前用户的订单，支持分页和状态筛选。

    Args:
        page: 页码（从1开始）
        page_size: 每页数量（1-100）
        status_filter: 状态筛选（可选）
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 订单列表（包含分页信息）
    """
    try:
        from sqlalchemy import select, func, desc
        from app.models.order import Order

        # 构建查询
        query = select(Order).where(Order.user_id == str(current_user.id))

        # 添加状态筛选
        if status_filter:
            query = query.where(Order.status == status_filter)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 添加排序和分页
        query = query.order_by(desc(Order.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        # 执行查询
        result = await db.execute(query)
        orders = result.scalars().all()

        # 加载订单明细
        order_responses = []
        temp_service = OrderService()
        for order in orders:
            await temp_service._load_order_items(db, order)
            order_response = temp_service._order_to_response(order)
            order_responses.append(order_response.model_dump())

        # 返回成功响应
        return success_response(
            data={
                "items": order_responses,
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size  # 向上取整
            },
            message="获取订单列表成功"
        )

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing orders for user {current_user.id}: {e}")

        # 返回友好错误信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单列表失败，请稍后重试"
        )


@router.get(
    "/{order_id}",
    response_model=Dict[str, Any],
    summary="获取订单详情",
    description="获取指定订单的详细信息，包含订单明细"
)
async def get_order_detail_endpoint(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取订单详情

    返回指定订单的详细信息，包含订单明细。
    只能查看自己的订单。

    Args:
        order_id: 订单ID
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 订单详细信息

    Raises:
        NotFoundException: 订单不存在
        BusinessException: 无权访问此订单
    """
    try:
        # 初始化订单服务
        order_service = OrderService()

        # 获取订单详情
        order = await order_service.get_order(
            db=db,
            order_id=order_id,
            user_id=str(current_user.id)
        )

        # 返回成功响应
        return success_response(
            data=order.model_dump(),
            message="获取订单详情成功"
        )

    except (NotFoundException, BusinessException) as e:
        # 业务异常直接抛出
        raise e

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting order {order_id} for user {current_user.id}: {e}")

        # 返回友好错误信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单详情失败，请稍后重试"
        )


@router.put(
    "/{order_id}/cancel",
    response_model=Dict[str, Any],
    summary="取消订单",
    description="取消指定的订单（仅未支付订单可取消）"
)
async def cancel_order_endpoint(
    order_id: str,
    cancel_request: CancelOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    取消订单

    取消指定的订单并释放库存锁定。
    只有未支付的订单才能取消。

    Args:
        order_id: 订单ID
        cancel_request: 取消请求（包含可选的取消原因）
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 取消后的订单信息

    Raises:
        NotFoundException: 订单不存在
        BusinessException: 无权取消、状态不允许取消
    """
    try:
        # 初始化订单服务
        order_service = OrderService()

        # 取消订单
        order = await order_service.cancel_order(
            db=db,
            order_id=order_id,
            user_id=str(current_user.id),
            reason=cancel_request.reason or "用户取消"
        )

        # 返回成功响应
        return success_response(
            data=order.model_dump(),
            message="订单已取消"
        )

    except (NotFoundException, BusinessException) as e:
        # 业务异常直接抛出
        raise e

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error cancelling order {order_id} for user {current_user.id}: {e}")

        # 返回友好错误信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消订单失败，请稍后重试"
        )


@router.get(
    "/{order_id}/status",
    response_model=Dict[str, Any],
    summary="获取订单状态",
    description="获取指定订单的当前状态信息"
)
async def get_order_status_endpoint(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取订单状态

    返回指定订单的状态信息，包括订单状态、支付状态等。
    只能查看自己的订单状态。

    Args:
        order_id: 订单ID
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 订单状态信息

    Raises:
        NotFoundException: 订单不存在
        BusinessException: 无权访问此订单
    """
    try:
        # 初始化订单服务
        order_service = OrderService()

        # 获取订单详情
        order = await order_service.get_order(
            db=db,
            order_id=order_id,
            user_id=str(current_user.id)
        )

        # 返回状态信息
        return success_response(
            data={
                "order_id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "payment_status": order.payment_status,
                "transaction_id": order.transaction_id,
                "paid_at": order.paid_at,
                "created_at": order.created_at,
                "updated_at": order.updated_at
            },
            message="获取订单状态成功"
        )

    except (NotFoundException, BusinessException) as e:
        # 业务异常直接抛出
        raise e

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting status for order {order_id} for user {current_user.id}: {e}")

        # 返回友好错误信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单状态失败，请稍后重试"
        )
