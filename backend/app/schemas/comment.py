"""
评论 - 与迭代规划 2.2、技术方案 2.1.1 一致；二级回复用 parent_id
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    """发表评论或回复：根评论不传 parent_id，回复传 parent_id"""
    content: str = Field(..., min_length=1, max_length=500)
    parent_id: Optional[str] = Field(None, description="回复某条评论时传父评论 id")


class CommentResponse(BaseModel):
    id: str
    post_id: str
    user_id: str
    anonymous_name: str
    content: str
    parent_id: Optional[str] = None
    like_count: int
    risk_status: str
    created_at: datetime
    updated_at: datetime
    replies: Optional[List["CommentResponse"]] = None

    class Config:
        from_attributes = True


# 列表项：根评论可带 replies
CommentResponse.model_rebuild()
