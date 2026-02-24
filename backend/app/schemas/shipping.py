"""
物流和退货 - 请求/响应模型
Shipping and Returns - Request/Response Schemas

包含所有物流和退货相关的Pydantic模型：
- ShipmentCreate - 创建发货记录
- ShipmentResponse - 发货记录响应
- TrackingUpdate - 更新物流状态
- ReturnCreate - 创建退货申请
- ReturnResponse - 退货记录响应
- ReturnApprove - 审批退货
- ReturnReject - 拒绝退货
- RefundProcess - 处理退款
"""
from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer


class ShipmentCreate(BaseModel):
    """创建发货记录请求"""
    courier_code: str = Field(..., min_length=1, max_length=20, description="物流公司代码")
    tracking_number: str = Field(..., min_length=1, max_length=50, description="物流单号")


class ShipmentResponse(BaseModel):
    """发货记录响应"""
    id: str
    order_id: str
    courier_code: str
    courier_name: str
    tracking_number: str
    status: str
    shipped_at: datetime
    delivered_at: Optional[datetime] = None
    tracking_info: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True


class TrackingUpdate(BaseModel):
    """更新物流状态请求"""
    status: Literal["pending", "picked_up", "in_transit", "delivered", "failed"] = Field(
        ..., description="物流状态"
    )
    tracking_info: Optional[List[Dict[str, Any]]] = Field(
        None, description="物流跟踪详情"
    )


class ReturnCreate(BaseModel):
    """创建退货申请请求"""
    order_item_id: str = Field(..., description="订单明细ID")
    reason: Literal[
        "quality_issue", "damaged", "wrong_item",
        "not_as_described", "no_longer_needed", "other"
    ] = Field(..., description="退货原因")
    return_type: Literal["refund_only", "replace", "return_and_refund"] = Field(
        ..., description="退货类型"
    )
    description: Optional[str] = Field(None, max_length=500, description="退货说明")
    images: Optional[List[str]] = Field(None, description="凭证图片URL列表")


class ReturnResponse(BaseModel):
    """退货记录响应"""
    id: str
    order_id: str
    order_item_id: str
    return_reason: str
    return_description: Optional[str] = None
    images: Optional[List[str]] = None
    return_type: str
    status: str
    refund_amount: Optional[Decimal] = None
    refund_transaction_id: Optional[str] = None
    requested_at: datetime
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    admin_id: Optional[str] = None
    admin_notes: Optional[str] = None

    class Config:
        from_attributes = True

    @field_serializer('refund_amount')
    def serialize_refund_amount(self, value: Optional[Decimal]) -> Optional[str]:
        """Serialize refund_amount Decimal to string"""
        if value is None:
            return None
        return str(value)


class ReturnApprove(BaseModel):
    """审批退货请求"""
    notes: Optional[str] = Field(None, max_length=500, description="管理员备注")


class ReturnReject(BaseModel):
    """拒绝退货请求"""
    notes: Optional[str] = Field(None, max_length=500, description="拒绝原因")


class RefundProcess(BaseModel):
    """处理退款请求"""
    refund_amount: Decimal = Field(..., gt=0, description="退款金额")
    transaction_id: Optional[str] = Field(None, max_length=100, description="退款交易ID")

    @field_validator("refund_amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """验证退款金额"""
        if v <= 0:
            raise ValueError("退款金额必须大于0")
        return v
