"""
购物车接口 - Sprint 3.7 电商订单系统
Shopping Cart API Endpoints

提供购物车相关的所有API端点：
- GET /cart - 获取用户购物车
- POST /cart/items - 添加商品到购物车
- PUT /cart/items/{item_id} - 更新购物车商品数量
- DELETE /cart/items/{item_id} - 移除购物车商品
- DELETE /cart - 清空购物车

关键特性：
- 使用Redis存储购物车数据
- 集成库存锁定服务
- 支持积分商品和现金商品
- 自动计算总金额、总积分、商品数量
- JWT认证保护所有端点
"""
from typing import Any, Dict

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import (BusinessException, NotFoundException, ValidationException,
                                 success_response)
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse
from app.services.cart_service import CartService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/cart", tags=["shopping-cart"])


@router.get(
    "",
    response_model=Dict[str, Any],
    summary="获取用户购物车",
    description="获取当前用户的购物车，包含所有商品和 totals 信息"
)
async def get_cart_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取用户购物车

    返回购物车中的所有商品，以及总金额、总积分、商品总数等信息。

    Args:
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 包含购物车信息的响应

    Raises:
        HTTPException: Redis连接失败等错误
    """
    try:
        # 初始化购物车服务
        cart_service = CartService()

        # 获取购物车
        cart = await cart_service.get_cart(user_id=str(current_user.id))

        # 转换为响应格式
        return success_response(
            data={
                "items": [item.model_dump() for item in cart.items],
                "total_amount": cart.total_amount,
                "total_points": cart.total_points,
                "item_count": cart.item_count,
            },
            message="获取购物车成功"
        )

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting cart for user {current_user.id}: {e}")

        # 返回友好错误信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取购物车失败，请稍后重试"
        )


@router.post(
    "/items",
    response_model=Dict[str, Any],
    summary="添加商品到购物车",
    description="将指定SKU商品添加到购物车，如果已存在则增加数量"
)
async def add_item_to_cart_endpoint(
    body: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    添加商品到购物车

    如果商品已存在于购物车中，则增加数量；否则添加新商品。
    添加时会锁定相应的库存。

    Args:
        body: 购物车项创建请求（sku_id, quantity）
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 更新后的购物车信息

    Raises:
        ValidationException: 请求数据验证失败
        NotFoundException: SKU或商品不存在
        BusinessException: 库存不足、商品已下架等业务错误
    """
    try:
        # 初始化购物车服务
        cart_service = CartService()

        # 添加商品到购物车
        cart = await cart_service.add_item(
            db=db,
            user_id=str(current_user.id),
            sku_id=body.sku_id,
            quantity=body.quantity,
        )

        # 转换为响应格式
        return success_response(
            data={
                "items": [item.model_dump() for item in cart.items],
                "total_amount": cart.total_amount,
                "total_points": cart.total_points,
                "item_count": cart.item_count,
            },
            message="添加到购物车成功"
        )

    except NotFoundException as e:
        # SKU或商品不存在
        raise e

    except BusinessException as e:
        # 业务错误（库存不足、商品已下架等）
        raise e

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error adding item to cart for user {current_user.id}: {e}")

        # 返回友好错误信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加到购物车失败，请稍后重试"
        )


@router.put(
    "/items/{item_id}",
    response_model=Dict[str, Any],
    summary="更新购物车商品数量",
    description="更新购物车中指定商品的数量，会自动锁定或释放库存"
)
async def update_cart_item_endpoint(
    item_id: str,
    body: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    更新购物车商品数量

    根据数量变化自动锁定或释放库存：
    - 数量增加：锁定新增的库存
    - 数量减少：释放减少的库存

    Args:
        item_id: 购物车项ID
        body: 更新请求（新的quantity）
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 更新后的购物车信息

    Raises:
        ValidationException: 请求数据验证失败
        NotFoundException: 购物车项不存在
        BusinessException: 库存不足等业务错误
    """
    try:
        # 初始化购物车服务
        cart_service = CartService()

        # 更新购物车商品数量
        cart = await cart_service.update_item(
            user_id=str(current_user.id),
            item_id=item_id,
            quantity=body.quantity,
        )

        # 转换为响应格式
        return success_response(
            data={
                "items": [item.model_dump() for item in cart.items],
                "total_amount": cart.total_amount,
                "total_points": cart.total_points,
                "item_count": cart.item_count,
            },
            message="更新购物车成功"
        )

    except NotFoundException as e:
        # 购物车项不存在
        raise e

    except BusinessException as e:
        # 业务错误（库存不足等）
        raise e

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating cart item {item_id} for user {current_user.id}: {e}")

        # 返回友好错误信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新购物车失败，请稍后重试"
        )


@router.delete(
    "/items/{item_id}",
    response_model=Dict[str, Any],
    summary="移除购物车商品",
    description="从购物车中移除指定商品，释放相应的库存锁定"
)
async def remove_cart_item_endpoint(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    移除购物车商品

    从购物车中删除指定商品，并释放该商品的所有库存锁定。

    Args:
        item_id: 购物车项ID
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 更新后的购物车信息

    Raises:
        NotFoundException: 购物车项不存在
    """
    try:
        # 初始化购物车服务
        cart_service = CartService()

        # 移除购物车商品
        cart = await cart_service.remove_item(
            user_id=str(current_user.id),
            item_id=item_id,
        )

        # 转换为响应格式
        return success_response(
            data={
                "items": [item.model_dump() for item in cart.items],
                "total_amount": cart.total_amount,
                "total_points": cart.total_points,
                "item_count": cart.item_count,
            },
            message="移除商品成功"
        )

    except NotFoundException as e:
        # 购物车项不存在
        raise e

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error removing cart item {item_id} for user {current_user.id}: {e}")

        # 返回友好错误信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="移除商品失败，请稍后重试"
        )


@router.delete(
    "",
    response_model=Dict[str, Any],
    summary="清空购物车",
    description="清空用户购物车中的所有商品，释放所有库存锁定"
)
async def clear_cart_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    清空购物车

    删除购物车中的所有商品，并释放所有商品的库存锁定。

    Args:
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 操作结果
    """
    try:
        # 初始化购物车服务
        cart_service = CartService()

        # 清空购物车
        await cart_service.clear_cart(user_id=str(current_user.id))

        # 返回成功响应
        return success_response(message="购物车已清空")

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error clearing cart for user {current_user.id}: {e}")

        # 返回友好错误信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清空购物车失败，请稍后重试"
        )
