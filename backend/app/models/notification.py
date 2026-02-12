"""
通知表 - 与迭代规划 2.2 数据模型一致，技术方案 2.2.1 按 user_id 哈希分表（当前先单表）
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, ForeignKey

from .base import Base
from .user import gen_uuid


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(
        Enum("comment", "reply", "like", "system", name="notification_type_enum"),
        nullable=False,
    )
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=True)
    related_id = Column(String(36), nullable=True, comment="关联帖子/评论 id")
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
