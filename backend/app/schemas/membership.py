"""
会员请求/响应模型 - Sprint 3.5
"""
from typing import Optional
from pydantic import BaseModel, Field


class MembershipItem(BaseModel):
    """会员套餐项"""
    id: str
    name: str
    description: Optional[str]
    price: float
    duration_days: int
    is_active: bool


class MembershipListResponse(BaseModel):
    """会员列表响应"""
    items: list[MembershipItem]


class MembershipOrderCreate(BaseModel):
    """创建会员订单请求"""
    membership_id: str
    amount: float
    payment_method: str = "wechat"
    transaction_id: Optional[str] = None


class MembershipOrderItem(BaseModel):
    """会员订单项"""
    id: str
    membership_id: str
    amount: float
    status: str
    start_date: str
    end_date: Optional[str]
    auto_renew: bool
    created_at: str


# Aliases for admin API
MembershipCreate = MembershipOrderCreate
MembershipResponse = MembershipItem
