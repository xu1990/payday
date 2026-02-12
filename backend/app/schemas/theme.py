"""
主题与设置 - 请求/响应模型；Sprint 3.4
"""
from typing import Optional
from pydantic import BaseModel, Field


class ThemeItem(BaseModel):
    """主题项"""
    id: str
    name: str
    display_name: str
    preview_color: str
    primary_color: str
    is_dark: bool

    class Config:
        from_attributes = True


class ThemeListResponse(BaseModel):
    """主题列表响应"""
    items: list[ThemeItem]


class UserSettingsResponse(BaseModel):
    """用户设置响应"""
    theme_id: Optional[str] = None
    privacy_profile: int = 0
    allow_stranger_notice: int = 1
    allow_comment: int = 1

    class Config:
        from_attributes = True


class UserSettingsUpdate(BaseModel):
    """用户设置更新请求"""
    theme_id: Optional[str] = None
    privacy_profile: Optional[int] = None
    allow_stranger_notice: Optional[int] = None
    allow_comment: Optional[int] = None
