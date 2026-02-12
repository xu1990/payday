"""
通知 - 列表、未读数、标记已读
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str  # comment | reply | like | system
    title: str
    content: Optional[str] = None
    related_id: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int


class MarkReadBody(BaseModel):
    """标记已读：传 ids 为部分已读，传 all=true 为全部已读"""
    notification_ids: Optional[List[str]] = Field(None, description="要标记已读的通知 id 列表")
    all: Optional[bool] = Field(None, description="为 true 时标记当前用户全部已读")
