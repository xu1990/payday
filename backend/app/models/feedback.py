"""
用户反馈表
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.mysql import JSON

from .base import Base
from .user import gen_uuid


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), nullable=False, index=True, comment="用户ID")
    content = Column(Text, nullable=False, comment="反馈内容")
    images = Column(JSON, nullable=True, comment="反馈图片列表")
    contact = Column(String(100), nullable=True, comment="联系方式")
    status = Column(String(20), default="pending", comment="状态: pending/processing/resolved")
    admin_reply = Column(Text, nullable=True, comment="管理员回复")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
