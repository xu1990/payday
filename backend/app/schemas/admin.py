"""管理端 - 登录、用户列表/详情、工资列表、统计"""
from datetime import date, datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    csrf_token: str  # CSRF token 用于保护状态变更操作


class AdminUserListItem(BaseModel):
    id: str
    openid: str
    anonymous_name: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminUserDetail(AdminUserListItem):
    unionid: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    allow_follow: int = 1
    allow_comment: int = 1
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminSalaryRecordItem(BaseModel):
    id: str
    user_id: str
    config_id: str
    amount: float
    payday_date: date
    salary_type: str
    risk_status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminSalaryRecordUpdateRiskRequest(BaseModel):
    """管理端工资记录人工审核"""
    risk_status: str  # approved | rejected


class AdminStatisticsResponse(BaseModel):
    user_total: int
    user_new_today: int
    salary_record_total: int
    salary_record_today: int


# ----- 帖子管理（Sprint 2.4） -----


class AdminPostListItem(BaseModel):
    id: str
    user_id: str
    anonymous_name: str
    content: str
    images: Optional[List[str]] = None
    type: str
    view_count: int
    like_count: int
    comment_count: int
    status: str
    risk_status: str
    risk_score: Optional[int] = None
    risk_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminPostListResponse(BaseModel):
    items: List[AdminPostListItem]
    total: int


class AdminPostUpdateStatusRequest(BaseModel):
    """管理端更新帖子：status 和/或 风控人工审核"""
    status: Optional[str] = None  # normal | hidden | deleted
    risk_status: Optional[str] = None  # approved | rejected
    risk_reason: Optional[str] = None


# ----- 评论管理（Sprint 2.4） -----


class AdminCommentListItem(BaseModel):
    id: str
    post_id: str
    user_id: str
    anonymous_name: str
    content: str
    parent_id: Optional[str] = None
    like_count: int
    risk_status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminCommentListResponse(BaseModel):
    items: List[AdminCommentListItem]
    total: int


class AdminCommentUpdateRiskRequest(BaseModel):
    risk_status: Literal["approved", "rejected"]  # approved | rejected
    risk_reason: Optional[str] = None


# ----- 风控待审（Sprint 2.4） -----


class AdminPendingPostItem(AdminPostListItem):
    """待审帖子（与帖子列表项一致，便于前端复用）"""
    pass


class AdminPendingCommentItem(AdminCommentListItem):
    """待审评论"""
    pass
