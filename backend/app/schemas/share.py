"""
分享请求/响应模型 - P1-2 分享功能
"""
from typing import Optional, Literal, List
from datetime import datetime
from pydantic import BaseModel, Field


class ShareCreate(BaseModel):
    """创建分享记录请求"""
    target_type: str = Field(..., description="分享目标类型：post/salary/poster")
    target_id: str = Field(..., description="分享目标ID")
    share_channel: str = Field(..., description="分享渠道：wechat_friend/wechat_moments")


class ShareUpdateStatus(BaseModel):
    """更新分享状态请求"""
    status: Literal["success", "failed"] = Field(..., description="分享状态")
    error_message: Optional[str] = Field(None, description="失败原因（可选）")


class ShareResponse(BaseModel):
    """分享记录响应"""
    id: str
    user_id: str
    target_type: str
    target_id: str
    share_channel: str
    share_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ShareListResponse(BaseModel):
    """分享记录列表响应"""
    items: List[ShareResponse]
    total: int


class ShareStatsResponse(BaseModel):
    """分享统计响应"""
    total_shares: int
    success_shares: int
    success_rate: str
    days: int
