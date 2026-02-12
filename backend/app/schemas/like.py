"""
点赞 - 仅用于响应；点赞/取消通过 POST/DELETE 完成，无请求体
"""
from datetime import datetime

from pydantic import BaseModel


class LikeResponse(BaseModel):
    id: str
    user_id: str
    target_type: str  # post | comment
    target_id: str
    created_at: datetime

    class Config:
        from_attributes = True
