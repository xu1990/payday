"""
帖子 - 请求/响应模型；与迭代规划 2.2、技术方案 2.2.1 一致
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    """发帖：anonymous_name 由服务端用当前用户匿名昵称填充"""
    content: str = Field(..., min_length=1, max_length=5000, description="帖子内容，1-5000字符")
    images: Optional[List[str]] = Field(None, max_length=9, description="图片列表，最多9张")
    tags: Optional[List[str]] = Field(None, max_length=10, description="标签列表，最多10个")
    type: Literal["complaint", "sharing", "question"] = "complaint"
    salary_range: Optional[str] = Field(None, max_length=20, description="工资区间")
    industry: Optional[str] = Field(None, max_length=50, description="行业")
    city: Optional[str] = Field(None, max_length=50, description="城市")
    visibility: Literal["public", "followers", "private"] = "public"


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
    visibility: str
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
