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


class PaymentMode(str, Enum):
    """支付模式枚举"""
    POINTS_ONLY = "points_only"
    CASH_ONLY = "cash_only"
    MIXED = "mixed"


class PaymentStatus(str, Enum):
    """支付状态枚举"""
    UNPAID = "unpaid"
    PAYING = "paying"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class PointOrderCreate(BaseModel):
    """创建订单Schema"""
    product_id: str = Field(..., description="商品ID")
    sku_id: Optional[str] = Field(None, description="SKU ID")
    address_id: Optional[str] = Field(None, description="收货地址ID")
    delivery_info: Optional[str] = Field(None, description="收货信息")
    notes: Optional[str] = Field(None, description="备注")
    idempotency_key: Optional[str] = Field(None, description="幂等性键（防重复提交）")
    payment_mode: Optional[str] = Field(None, description="支付模式（可选，默认使用商品设置）")


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

    # 支付信息（新增）
    payment_mode: PaymentMode
    points_deducted: bool = False
    cash_amount: Optional[int] = None
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None

    # 退款信息（新增）
    refund_status: Optional[str] = None
    refund_amount: Optional[int] = None
    refund_transaction_id: Optional[str] = None
    refunded_at: Optional[datetime] = None

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

    # 支付信息（新增）
    payment_mode: PaymentMode
    cash_amount: Optional[int] = None
    payment_status: PaymentStatus = PaymentStatus.UNPAID

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