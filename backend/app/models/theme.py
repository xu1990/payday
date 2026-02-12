"""
主题表 - Sprint 3.4 主题与设置
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey

from .base import Base
from .user import gen_uuid


class Theme(Base):
    __tablename__ = "themes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(50), nullable=False, comment="主题名称")
    display_name = Column(String(50), nullable=False, comment="显示名称")
    preview_color = Column(String(20), nullable=False, comment="预览色")
    primary_color = Column(String(20), nullable=False, comment="主色调")
    is_dark = Column(Integer, default=0, nullable=False, comment="是否暗色主题")
    is_system = Column(Integer, default=0, nullable=False, comment="是否系统主题")
    created_at = Column(DateTime, default=datetime.utcnow)


class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    theme_id = Column(String(36), ForeignKey("themes.id"), nullable=True, comment="当前主题ID")
    privacy_profile = Column(Integer, default=0, nullable=False, comment="隐私资料可见性：0=公开 1=仅好友")
    allow_stranger_notice = Column(Integer, default=1, nullable=False, comment="是否允许陌生人私信")
    allow_comment = Column(Integer, default=1, nullable=False, comment="是否允许评论")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
