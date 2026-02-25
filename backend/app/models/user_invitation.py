"""用户邀请关系表 - Sprint 4.7 邀请系统"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String

from .base import Base
from .user import gen_uuid


class UserInvitation(Base):
    """用户邀请关系记录表"""

    __tablename__ = "user_invitations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    inviter_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="邀请者ID")
    invitee_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True, comment="被邀请者ID")
    invite_code_used = Column(String(12), nullable=False, comment="使用的邀请码")

    # 奖励状态
    inviter_points_rewarded = Column(String(36), nullable=True, comment="邀请者积分流水ID")
    invitee_points_rewarded = Column(String(36), nullable=True, comment="被邀请者积分流水ID")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")

    # 关系
    inviter = None  # relationship("User", foreign_keys=[inviter_id])
    invitee = None  # relationship("User", foreign_keys=[invitee_id])

    # 复合索引 - 快速查询是否已邀请过某人
    __table_args__ = (
        Index('ix_user_invitations_inviter_invitee', 'inviter_id', 'invitee_id'),
    )
