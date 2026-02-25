"""
物流跟踪Schemas - Tracking Schemas
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TrackingEvent(BaseModel):
    """物流跟踪事件"""
    status: str = Field(..., description="事件状态")
    description: str = Field(..., description="事件描述")
    location: Optional[str] = Field(None, description="事件地点")
    timestamp: datetime = Field(..., description="事件时间")

    class Config:
        from_attributes = True


class TrackingInfo(BaseModel):
    """物流跟踪信息"""
    tracking_number: str = Field(..., description="物流单号")
    courier_code: str = Field(..., description="物流公司代码")
    current_status: str = Field(..., description="当前状态")
    estimated_delivery: Optional[datetime] = Field(None, description="预计送达时间")
    events: List[TrackingEvent] = Field(default_factory=list, description="跟踪事件列表")

    class Config:
        from_attributes = True


class TrackingInfoResponse(BaseModel):
    """物流跟踪信息响应"""
    success: bool = Field(True, description="是否成功")
    data: TrackingInfo = Field(..., description="物流信息")


class ShipmentCreate(BaseModel):
    """创建物流跟踪"""
    order_id: int = Field(..., description="订单ID")
    courier_code: str = Field(..., description="物流公司代码")
    courier_name: str = Field(..., description="物流公司名称")
    tracking_number: str = Field(..., description="物流单号")


class ShipmentResponse(BaseModel):
    """物流跟踪响应"""
    id: int
    order_id: int
    courier_code: str
    courier_name: str
    tracking_number: str
    status: str
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    estimated_delivery: Optional[datetime]
    last_updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ShipmentDetailResponse(ShipmentResponse):
    """物流跟踪详情响应"""
    events: List[TrackingEvent] = Field(default_factory=list, description="跟踪事件列表")
