"""
物流和退货接口 - Task 4.3 Phase 4
Shipping and Returns API Endpoints

提供物流和退货相关的所有API端点：
- POST /orders/{order_id}/shipment - 创建发货记录（管理员）
- GET /orders/{order_id}/shipment - 获取发货信息
- PUT /shipments/{shipment_id}/tracking - 更新物流状态（管理员）
- POST /orders/{order_id}/returns - 创建退货申请
- GET /orders/{order_id}/returns - 获取退货列表
- PUT /returns/{return_id}/approve - 审批退货（管理员）
- PUT /returns/{return_id}/reject - 拒绝退货（管理员）
- POST /returns/{return_id}/refund - 处理退款（管理员）

关键特性：
- 使用ShippingService处理业务逻辑
- JWT认证保护所有端点
- 管理员和用户权限分离
- 完整的退货流程管理
- 统一错误处理
"""
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.core.exceptions import (
    success_response,
    NotFoundException,
    BusinessException,
    ValidationException,
)
from app.models.user import User
from app.models.admin import AdminUser
from app.schemas.shipping import (
    ShipmentCreate,
    ShipmentResponse,
    TrackingUpdate,
    ReturnCreate,
    ReturnResponse,
    ReturnApprove,
    ReturnReject,
    RefundProcess,
)
from app.services.shipping_service import ShippingService

router = APIRouter(tags=["shipping"])


# ==================== 发货记录相关接口 ====================

@router.post(
    "/orders/{order_id}/shipment",
    response_model=Dict[str, Any],
    summary="创建发货记录",
    description="管理员为订单创建发货记录，订单必须已支付且未发货"
)
async def create_shipment_endpoint(
    order_id: str,
    shipment_data: ShipmentCreate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    创建发货记录（管理员）

    流程：
    1. 验证订单存在且已支付
    2. 检查订单未发货（防止重复发货）
    3. 验证物流公司存在
    4. 创建发货记录
    5. 更新订单状态为shipped

    Args:
        order_id: 订单ID
        shipment_data: 发货数据（物流公司代码、物流单号）
        current_admin: 当前认证管理员
        db: 数据库session

    Returns:
        Dict: 创建的发货记录

    Raises:
        NotFoundException: 订单或物流公司不存在
        BusinessException: 订单未支付、已发货
    """
    try:
        # 初始化物流服务
        shipping_service = ShippingService()

        # 创建发货记录
        shipment = await shipping_service.create_shipment(
            db=db,
            order_id=order_id,
            courier_code=shipment_data.courier_code,
            tracking_number=shipment_data.tracking_number
        )

        # 返回成功响应
        return success_response(
            data=ShipmentResponse.model_validate(shipment).model_dump(mode='json'),
            message="发货成功"
        )

    except (NotFoundException, BusinessException) as e:
        # 业务异常直接抛出
        raise e

    except Exception as e:
        # 记录错误日志
        import logging
        logging.error(f"Error creating shipment for order {order_id}: {e}")
        raise BusinessException(
            "创建发货记录失败",
            code="SHIPMENT_CREATE_FAILED"
        )


@router.get(
    "/orders/{order_id}/shipment",
    response_model=Dict[str, Any],
    summary="获取发货信息",
    description="获取订单的发货记录和物流信息"
)
async def get_shipment_endpoint(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取发货信息

    Args:
        order_id: 订单ID
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 发货记录信息

    Raises:
        NotFoundException: 发货记录不存在
    """
    try:
        # 初始化物流服务
        shipping_service = ShippingService()

        # 根据订单ID获取发货记录
        shipment = await shipping_service.get_shipment_by_order_id(
            db=db,
            order_id=order_id
        )

        if not shipment:
            raise NotFoundException("发货记录不存在")

        # 返回成功响应
        return success_response(
            data=ShipmentResponse.model_validate(shipment).model_dump(mode='json'),
            message="获取发货信息成功"
        )

    except NotFoundException:
        raise

    except Exception as e:
        import logging
        logging.error(f"Error getting shipment for order {order_id}: {e}")
        raise BusinessException(
            "获取发货信息失败",
            code="SHIPMENT_GET_FAILED"
        )


@router.put(
    "/shipments/{shipment_id}/tracking",
    response_model=Dict[str, Any],
    summary="更新物流状态",
    description="管理员或webhook更新发货记录的物流状态"
)
async def update_tracking_endpoint(
    shipment_id: str,
    tracking_data: TrackingUpdate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    更新物流状态（管理员）

    流程：
    1. 验证发货记录存在
    2. 验证状态有效
    3. 更新物流状态和跟踪信息
    4. 如果状态为已签收，更新订单状态

    Args:
        shipment_id: 发货记录ID
        tracking_data: 物流状态数据
        current_admin: 当前认证管理员
        db: 数据库session

    Returns:
        Dict: 更新后的发货记录

    Raises:
        NotFoundException: 发货记录不存在
        ValidationException: 无效的物流状态
    """
    try:
        # 初始化物流服务
        shipping_service = ShippingService()

        # 更新物流状态
        shipment = await shipping_service.update_tracking_status(
            db=db,
            shipment_id=shipment_id,
            status=tracking_data.status,
            tracking_info=tracking_data.tracking_info
        )

        # 返回成功响应
        return success_response(
            data=ShipmentResponse.model_validate(shipment).model_dump(mode='json'),
            message="物流状态更新成功"
        )

    except (NotFoundException, ValidationException) as e:
        # 业务异常直接抛出
        raise e

    except Exception as e:
        import logging
        logging.error(f"Error updating tracking for shipment {shipment_id}: {e}")
        raise BusinessException(
            "更新物流状态失败",
            code="TRACKING_UPDATE_FAILED"
        )


# ==================== 退货相关接口 ====================

@router.post(
    "/orders/{order_id}/returns",
    response_model=Dict[str, Any],
    summary="创建退货申请",
    description="用户为已签收订单创建退货申请"
)
async def create_return_request_endpoint(
    order_id: str,
    return_data: ReturnCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    创建退货申请

    流程：
    1. 验证订单存在
    2. 验证订单项存在
    3. 验证订单所有权
    4. 验证订单已签收
    5. 验证退货原因和类型有效
    6. 创建退货申请

    Args:
        order_id: 订单ID
        return_data: 退货申请数据
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 创建的退货申请

    Raises:
        NotFoundException: 订单或订单项不存在
        BusinessException: 无权访问、订单未签收
        ValidationException: 无效的退货原因或类型
    """
    try:
        # 初始化物流服务
        shipping_service = ShippingService()

        # 创建退货申请
        return_request = await shipping_service.create_return_request(
            db=db,
            order_id=order_id,
            order_item_id=return_data.order_item_id,
            reason=return_data.reason,
            return_type=return_data.return_type,
            description=return_data.description,
            images=return_data.images,
            user_id=str(current_user.id)
        )

        # 返回成功响应
        return success_response(
            data=ReturnResponse.model_validate(return_request).model_dump(mode='json'),
            message="退货申请提交成功"
        )

    except (NotFoundException, BusinessException, ValidationException) as e:
        # 业务异常直接抛出
        raise e

    except Exception as e:
        import logging
        logging.error(f"Error creating return request for order {order_id}: {e}")
        raise BusinessException(
            "创建退货申请失败",
            code="RETURN_CREATE_FAILED"
        )


@router.get(
    "/orders/{order_id}/returns",
    response_model=Dict[str, Any],
    summary="获取退货列表",
    description="获取订单的所有退货记录"
)
async def get_returns_endpoint(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取退货列表

    Args:
        order_id: 订单ID
        current_user: 当前认证用户
        db: 数据库session

    Returns:
        Dict: 退货记录列表

    Raises:
        NotFoundException: 订单不存在
    """
    try:
        # 初始化物流服务
        shipping_service = ShippingService()

        # 获取退货列表
        returns = await shipping_service.get_returns_by_order(
            db=db,
            order_id=order_id
        )

        # 返回成功响应
        return success_response(
            data=[
                ReturnResponse.model_validate(ret).model_dump(mode='json')
                for ret in returns
            ],
            message="获取退货列表成功"
        )

    except NotFoundException:
        raise

    except Exception as e:
        import logging
        logging.error(f"Error getting returns for order {order_id}: {e}")
        raise BusinessException(
            "获取退货列表失败",
            code="RETURNS_GET_FAILED"
        )


@router.put(
    "/returns/{return_id}/approve",
    response_model=Dict[str, Any],
    summary="审批退货",
    description="管理员审批通过退货申请"
)
async def approve_return_endpoint(
    return_id: str,
    approve_data: ReturnApprove,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    审批退货（管理员）

    流程：
    1. 验证退货记录存在
    2. 验证状态允许审批
    3. 更新退货状态为approved
    4. 记录审批时间和管理员信息

    Args:
        return_id: 退货记录ID
        approve_data: 审批数据（备注）
        current_admin: 当前认证管理员
        db: 数据库session

    Returns:
        Dict: 更新后的退货记录

    Raises:
        NotFoundException: 退货记录不存在
        BusinessException: 状态不正确
    """
    try:
        # 初始化物流服务
        shipping_service = ShippingService()

        # 审批退货
        return_request = await shipping_service.approve_return(
            db=db,
            return_id=return_id,
            admin_id=str(current_admin.id),
            notes=approve_data.notes
        )

        # 返回成功响应
        return success_response(
            data=ReturnResponse.model_validate(return_request).model_dump(mode='json'),
            message="退货审批通过"
        )

    except (NotFoundException, BusinessException) as e:
        # 业务异常直接抛出
        raise e

    except Exception as e:
        import logging
        logging.error(f"Error approving return {return_id}: {e}")
        raise BusinessException(
            "审批退货失败",
            code="RETURN_APPROVE_FAILED"
        )


@router.put(
    "/returns/{return_id}/reject",
    response_model=Dict[str, Any],
    summary="拒绝退货",
    description="管理员拒绝退货申请"
)
async def reject_return_endpoint(
    return_id: str,
    reject_data: ReturnReject,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    拒绝退货（管理员）

    流程：
    1. 验证退货记录存在
    2. 验证状态允许拒绝
    3. 更新退货状态为rejected
    4. 记录管理员信息

    Args:
        return_id: 退货记录ID
        reject_data: 拒绝数据（原因）
        current_admin: 当前认证管理员
        db: 数据库session

    Returns:
        Dict: 更新后的退货记录

    Raises:
        NotFoundException: 退货记录不存在
        BusinessException: 状态不正确
    """
    try:
        # 初始化物流服务
        shipping_service = ShippingService()

        # 拒绝退货
        return_request = await shipping_service.reject_return(
            db=db,
            return_id=return_id,
            admin_id=str(current_admin.id),
            notes=reject_data.notes
        )

        # 返回成功响应
        return success_response(
            data=ReturnResponse.model_validate(return_request).model_dump(mode='json'),
            message="退货申请已拒绝"
        )

    except (NotFoundException, BusinessException) as e:
        # 业务异常直接抛出
        raise e

    except Exception as e:
        import logging
        logging.error(f"Error rejecting return {return_id}: {e}")
        raise BusinessException(
            "拒绝退货失败",
            code="RETURN_REJECT_FAILED"
        )


@router.post(
    "/returns/{return_id}/refund",
    response_model=Dict[str, Any],
    summary="处理退款",
    description="管理员处理已审批退货的退款"
)
async def process_refund_endpoint(
    return_id: str,
    refund_data: RefundProcess,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    处理退款（管理员）

    流程：
    1. 验证退货记录存在
    2. 验证状态允许退款
    3. 验证退款金额有效
    4. 更新退货状态为completed
    5. 记录退款金额和交易ID

    Args:
        return_id: 退货记录ID
        refund_data: 退款数据（金额、交易ID）
        current_admin: 当前认证管理员
        db: 数据库session

    Returns:
        Dict: 更新后的退货记录

    Raises:
        NotFoundException: 退货记录不存在
        BusinessException: 状态不正确
        ValidationException: 退款金额无效
    """
    try:
        # 初始化物流服务
        shipping_service = ShippingService()

        # 处理退款
        return_request = await shipping_service.process_refund(
            db=db,
            return_id=return_id,
            refund_amount=refund_data.refund_amount,
            transaction_id=refund_data.transaction_id
        )

        # 返回成功响应
        return success_response(
            data=ReturnResponse.model_validate(return_request).model_dump(mode='json'),
            message="退款处理成功"
        )

    except (NotFoundException, BusinessException, ValidationException) as e:
        # 业务异常直接抛出
        raise e

    except Exception as e:
        import logging
        logging.error(f"Error processing refund for return {return_id}: {e}")
        raise BusinessException(
            "处理退款失败",
            code="REFUND_PROCESS_FAILED"
        )
