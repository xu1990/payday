"""积分订单Schema - Sprint 4.7 商品兑换系统"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from app.models.point_order import PointOrder
from pydantic import BaseModel, Field, validator


class PointOrderStatus(str, Enum):
    """订单状态枚举"""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PointOrderCreate(BaseModel):
    """创建订单Schema"""
    product_id: str = Field(..., description="商品ID")
    delivery_info: Optional[str] = Field(None, description="收货信息")
    notes: Optional[str] = Field(None, description="备注")


class PointOrderUpdate(BaseModel):
    """更新订单Schema"""
    delivery_info: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[PointOrderStatus] = None
    notes_admin: Optional[str] = None


class PointOrderResponse(BaseModel):
    """订单响应Schema"""
    id: str
    user_id: str
    product_id: str
    order_number: str
    product_name: str
    product_image: Optional[str]
    points_cost: int
    delivery_info: Optional[str]
    sku_id: Optional[str]
    address_id: Optional[str]
    shipment_id: Optional[str]
    notes: Optional[str]
    status: PointOrderStatus
    admin_id: Optional[str]
    processed_at: Optional[datetime]
    notes_admin: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PointOrderListResponse(BaseModel):
    """订单列表响应Schema"""
    id: str
    order_number: str
    user_id: str
    product_name: str
    product_image: Optional[str]
    points_cost: int
    status: PointOrderStatus
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PointOrderAdminCreate(BaseModel):
    """管理员处理订单Schema"""
    action: str = Field(..., description="操作 (complete 或 cancel)")
    notes: Optional[str] = Field(None, description="处理备注")


class PointOrderStatistics(BaseModel):
    """订单统计Schema"""
    total_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    refunded_orders: int
    total_points_used: int