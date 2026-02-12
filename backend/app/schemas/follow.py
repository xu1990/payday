"""关注相关 schema - 列表项复用 UserResponse"""
from pydantic import BaseModel

from app.schemas.user import UserResponse


class FollowActionResponse(BaseModel):
    """关注/取关成功"""
    ok: bool = True
    following: bool  # 当前是否已关注


class FollowListResponse(BaseModel):
    """粉丝列表 / 关注列表"""
    items: list[UserResponse]
    total: int
