"""
分享记录表 - P1-2 分享功能
记录用户的分享行为（分享到微信好友、朋友圈等）
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer

from .base import Base
from .user import gen_uuid


class Share(Base):
    """分享记录表"""
    __tablename__ = "shares"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="分享用户ID")
    target_type = Column(String(20), nullable=False, comment="分享目标类型：post/salary/poster")
    target_id = Column(String(36), nullable=True, comment="分享目标ID（帖子ID/工资记录ID等）")
    share_channel = Column(String(20), nullable=False, comment="分享渠道：wechat_friend/wechat_moments")
    share_status = Column(String(20), default="pending", nullable=False, comment="分享状态：pending/success/failed")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    def __repr__(self):
        return f"<Share(id={self.id}, user={self.user_id}, type={self.target_type}, target={self.target_id}, channel={self.share_channel}, status={self.share_status})>"
