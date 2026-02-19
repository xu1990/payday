"""用户相关 schema"""
from typing import Optional

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: str
    anonymous_name: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    allow_follow: int = 1
    allow_comment: int = 1
    status: str = "normal"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    deactivated_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    anonymous_name: Optional[str] = Field(None, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)
    avatar: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=200)
    allow_follow: Optional[int] = None
    allow_comment: Optional[int] = None


class UserDeactivate(BaseModel):
    """用户注销请求"""
    pass  # 空请求体，仅确认操作
