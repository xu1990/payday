"""Ability Points Schemas - 能力值系统数据验证（Sprint 4.6）"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ============== Ability Point Response ==============
class AbilityPointResponse(BaseModel):
    """用户积分信息响应"""
    id: str
    user_id: str
    total_points: int
    available_points: int
    level: int
    total_earned: int
    total_spent: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============== Transaction Schemas ==============
class AbilityPointTransactionResponse(BaseModel):
    """积分流水响应"""
    id: str
    user_id: str
    amount: int
    balance_after: int
    transaction_type: str
    event_type: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============== Redemption Schemas ==============
class PointRedemptionCreate(BaseModel):
    """创建积分兑换请求"""
    reward_name: str = Field(..., min_length=1, max_length=100, description="奖励名称")
    reward_type: str = Field(..., description="奖励类型: coupon/gift/vip/etc.")
    points_cost: int = Field(..., gt=0, description="消耗积分")
    delivery_info: Optional[str] = Field(None, description="配送信息 JSON")
    notes: Optional[str] = Field(None, description="备注")


class PointRedemptionUpdate(BaseModel):
    """更新兑换状态（管理员）"""
    status: str = Field(..., pattern="^(pending|approved|completed|rejected)$")
    rejection_reason: Optional[str] = Field(None, description="拒绝原因")


class PointRedemptionResponse(BaseModel):
    """兑换记录响应"""
    id: str
    user_id: str
    reward_name: str
    reward_type: str
    points_cost: int
    status: str
    delivery_info: Optional[str] = None
    notes: Optional[str] = None
    admin_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============== Admin Schemas ==============
class AdminRedemptionListResponse(BaseModel):
    """管理员兑换列表响应"""
    redemptions: List[PointRedemptionResponse]
    total: int
    pending_count: int


# ============== Event Hook Schema ==============
class PointEvent(BaseModel):
    """积分事件（用于hooks系统）"""
    user_id: str
    event_type: str = Field(..., description="事件类型")
    points: int = Field(..., description="积分变动（正为获得，负为消费）")
    reference_id: Optional[str] = Field(None, description="关联记录ID")
    reference_type: Optional[str] = Field(None, description="关联记录类型")
    description: Optional[str] = Field(None, description="描述")
