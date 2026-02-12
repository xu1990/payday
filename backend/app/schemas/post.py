"""
帖子 - 请求/响应模型；与迭代规划 2.2、技术方案 2.2.1 一致
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    """发帖：anonymous_name 由服务端用当前用户匿名昵称填充"""
    content: str = Field(..., min_length=1, max_length=5000)
    images: Optional[List[str]] = Field(None, max_length=9)
    tags: Optional[List[str]] = None
    type: Literal["complaint", "sharing", "question"] = "complaint"
    salary_range: Optional[str] = Field(None, max_length=20)
    industry: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)


class PostResponse(BaseModel):
    id: str
    user_id: str
    anonymous_name: str
    content: str
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    type: str
    salary_range: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    view_count: int
    like_count: int
    comment_count: int
    status: str
    risk_status: str
    risk_score: Optional[int] = None
    risk_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
