"""
积分订单物流管理接口 - 管理后台
"""
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import NotFoundException, ValidationException, success_response
from app.models.shipping import OrderShipment
from app.models.user import User
from app.services.point_shipment_service import PointShipmentService
from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin/point-shipments", tags=["admin-point-shipments"])


# ==================== 请求/响应模型 ====================

class ShipmentCreate(BaseModel):
    """创建发货请求"""
    order_id: str = Field(..., description="订单ID")
    courier_code: str = Field(..., description="物流公司代码")
    tracking_number: str = Field(..., description="物流单号")


class ShipmentUpdate(BaseModel):
    """更新发货请求"""
    tracking_number: Optional[str] = Field(None, description="新的物流单号")
    status: Optional[str] = Field(None, description="发货状态")
    tracking_info: Optional[List[dict]] = Field(None, description="物流跟踪详情")


class ShipmentResponse(BaseModel):
    """发货记录响应"""
    id: str
    order_id: str
    courier_code: str
    courier_name: str
    tracking_number: str
    status: str
    shipped_at: Optional[str]
    delivered_at: Optional[str]
    tracking_info: Optional[List[dict]]
    created_at: str
    updated_at: str


class ShipmentListResponse(BaseModel):
    """发货列表响应"""
    shipments: List[ShipmentResponse]
    total: int
    has_more: bool


# ==================== API 端点 ====================

class PointOrderBasic(BaseModel):
    """待发货订单基本信息"""
    id: str
    order_number: str
    product_name: str
    status: str
    user_id: str


@router.get("/pending-orders", response_model=List[PointOrderBasic])
async def get_pending_point_orders(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取待发货订单列表（没有发货记录的已支付积分订单）"""
    try:
        from app.models.point_order import PointOrder
        from sqlalchemy import select

        # 获取已完成的积分订单（可以发货的订单）
        query = select(PointOrder).where(PointOrder.status == "completed")

        result = await db.execute(query)
        orders = result.scalars().all()

        # 过滤出没有发货记录的订单
        pending_orders = []
        for order in orders:
            # 检查是否已有发货记录
            shipment_query = select(OrderShipment).where(OrderShipment.order_id == order.id)
            shipment_result = await db.execute(shipment_query)
            existing_shipment = shipment_result.scalar_one_or_none()

            if not existing_shipment:
                pending_orders.append(order)

        return [
            PointOrderBasic(
                id=order.id,
                order_number=order.order_number,
                product_name=order.product_name or "",
                status=order.status,
                user_id=order.user_id
            )
            for order in pending_orders
        ]

    except Exception as e:
        raise ValidationException(f"获取待发货订单失败: {str(e)}")


@router.get("", response_model=ShipmentListResponse)
async def list_point_shipments(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    status: Optional[str] = Query(None, description="发货状态过滤"),
    courier_code: Optional[str] = Query(None, description="物流公司代码过滤"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取积分订单发货列表"""
    try:
        service = PointShipmentService()
        shipments = await service.list_shipments(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
            courier_code=courier_code
        )

        # Convert to response format
        shipment_responses = [
            ShipmentResponse(
                id=shipment.id,
                order_id=shipment.order_id,
                courier_code=shipment.courier_code,
                courier_name=shipment.courier_name,
                tracking_number=shipment.tracking_number,
                status=shipment.status,
                shipped_at=shipment.shipped_at.isoformat() if shipment.shipped_at else None,
                delivered_at=shipment.delivered_at.isoformat() if shipment.delivered_at else None,
                tracking_info=shipment.tracking_info,
                created_at=shipment.created_at.isoformat(),
                updated_at=shipment.updated_at.isoformat()
            )
            for shipment in shipments
        ]

        return ShipmentListResponse(
            shipments=shipment_responses,
            total=len(shipments),
            has_more=False  # Simple implementation - in production you'd check if there are more
        )

    except (ValidationException, NotFoundException):
        raise
    except Exception as e:
        raise ValidationException(f"获取发货列表失败: {str(e)}")


@router.post("/point-orders/{order_id}/ship", response_model=ShipmentResponse)
async def create_point_shipment(
    order_id: str = Path(..., description="订单ID"),
    shipment_data: ShipmentCreate = None,  # Pydantic will parse from request body
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """为积分订单创建发货记录"""
    try:
        service = PointShipmentService()
        shipment = await service.create_shipment(
            db=db,
            order_id=order_id,
            courier_code=shipment_data.courier_code,
            tracking_number=shipment_data.tracking_number
        )

        return ShipmentResponse(
            id=shipment.id,
            order_id=shipment.order_id,
            courier_code=shipment.courier_code,
            courier_name=shipment.courier_name,
            tracking_number=shipment.tracking_number,
            status=shipment.status,
            shipped_at=shipment.shipped_at.isoformat() if shipment.shipped_at else None,
            delivered_at=shipment.delivered_at.isoformat() if shipment.delivered_at else None,
            tracking_info=shipment.tracking_info,
            created_at=shipment.created_at.isoformat(),
            updated_at=shipment.updated_at.isoformat()
        )

    except (NotFoundException, ValidationException):
        raise
    except Exception as e:
        raise ValidationException(f"创建发货记录失败: {str(e)}")


@router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_point_shipment(
    shipment_id: str = Path(..., description="发货记录ID"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个发货记录"""
    try:
        service = PointShipmentService()
        shipment = await service.get_shipment(db=db, shipment_id=shipment_id)

        return ShipmentResponse(
            id=shipment.id,
            order_id=shipment.order_id,
            courier_code=shipment.courier_code,
            courier_name=shipment.courier_name,
            tracking_number=shipment.tracking_number,
            status=shipment.status,
            shipped_at=shipment.shipped_at.isoformat() if shipment.shipped_at else None,
            delivered_at=shipment.delivered_at.isoformat() if shipment.delivered_at else None,
            tracking_info=shipment.tracking_info,
            created_at=shipment.created_at.isoformat(),
            updated_at=shipment.updated_at.isoformat()
        )

    except NotFoundException:
        raise NotFoundException("发货记录不存在")
    except Exception as e:
        raise ValidationException(f"获取发货记录失败: {str(e)}")


@router.put("/{shipment_id}", response_model=ShipmentResponse)
async def update_point_shipment(
    shipment_id: str = Path(..., description="发货记录ID"),
    shipment_data: ShipmentUpdate = None,  # Pydantic will parse from request body
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新发货记录"""
    try:
        service = PointShipmentService()
        shipment = await service.update_shipment(
            db=db,
            shipment_id=shipment_id,
            tracking_number=shipment_data.tracking_number,
            status=shipment_data.status,
            tracking_info=shipment_data.tracking_info
        )

        return ShipmentResponse(
            id=shipment.id,
            order_id=shipment.order_id,
            courier_code=shipment.courier_code,
            courier_name=shipment.courier_name,
            tracking_number=shipment.tracking_number,
            status=shipment.status,
            shipped_at=shipment.shipped_at.isoformat() if shipment.shipped_at else None,
            delivered_at=shipment.delivered_at.isoformat() if shipment.delivered_at else None,
            tracking_info=shipment.tracking_info,
            created_at=shipment.created_at.isoformat(),
            updated_at=shipment.updated_at.isoformat()
        )

    except (NotFoundException, ValidationException):
        raise
    except Exception as e:
        raise ValidationException(f"更新发货记录失败: {str(e)}")


@router.get("/{shipment_id}/tracking")
async def get_point_shipment_tracking(
    shipment_id: str = Path(..., description="发货记录ID"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取物流跟踪信息"""
    try:
        service = PointShipmentService()
        tracking_info = await service.get_tracking_info(db=db, shipment_id=shipment_id)

        return success_response(
            data=tracking_info,
            message="获取物流跟踪信息成功"
        )

    except NotFoundException:
        raise NotFoundException("发货记录不存在")
    except Exception as e:
        raise ValidationException(f"获取物流跟踪信息失败: {str(e)}")