"""积分退货Schema - Sprint 4.7 商品兑换系统"""
from datetime import datetime
from typing import Optional

from app.models.point_return import PointReturn
from pydantic import BaseModel, Field


class PointReturnCreate(BaseModel):
    """创建退货申请Schema"""
    order_id: str = Field(..., description="订单ID")
    return_reason: str = Field(..., min_length=1, max_length=500, description="退货原因")
    refund_points: int = Field(..., gt=0, description="退还积分数量")
    notes: Optional[str] = Field(None, description="备注")

    @validator('refund_points')
    def validate_refund_points(cls, v, values):
        """验证退还积分数量"""
        # 这里应该调用service验证积分数量是否正确
        return v


class PointReturnUpdate(BaseModel):
    """更新退货申请Schema"""
    status: str = Field(..., description="处理状态 (pending, approved, rejected)")
    admin_notes: Optional[str] = Field(None, description="管理员备注")
    refund_points: Optional[int] = Field(None, gt=0, description="实际退还积分数量")


class PointReturnResponse(BaseModel):
    """退货申请响应Schema"""
    id: str
    order_id: str
    user_id: str
    return_reason: str
    refund_points: int
    return_status: str
    admin_notes: Optional[str]
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PointReturnListResponse(BaseModel):
    """退货申请列表响应Schema"""
    id: str
    order_id: str
    user_id: str
    return_reason: str
    refund_points: int
    return_status: str
    created_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True