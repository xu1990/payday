"""
推送通知表 - Sprint 3.5 运营功能
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey

from .base import Base
from .user import gen_uuid


class PushNotification(Base):
    __tablename__ = "push_notifications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(100), nullable=False, comment="推送标题")
    content = Column(Text, nullable=True, comment="推送内容")
    type = Column(
        String(20),
        nullable=False,
        comment="推送类型：system/promotion/payday",
    )
    target_type = Column(String(20), nullable=True, comment="跳转类型：post/user/web")
    target_id = Column(String(36), nullable=True, comment="跳转目标ID")
    is_sent = Column(Boolean, default=False, nullable=False, comment="是否已发送")
    sent_at = Column(DateTime, nullable=True, comment="发送时间")
    created_at = Column(DateTime, default=datetime.utcnow)
