"""
话题表 - Sprint 3.5 运营功能
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer

from .base import Base
from .user import gen_uuid


class Topic(Base):
    __tablename__ = "topics"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(50), nullable=False, comment="话题名称")
    description = Column(Text, nullable=True, comment="话题描述")
    cover_image = Column(String(500), nullable=True, comment="封面图片URL")
    post_count = Column(Integer, default=0, nullable=False, comment="关联帖子数")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
