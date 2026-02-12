"""
关注关系表 - 与 PRD 5.1.7、技术方案 2.3 一致
"""
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint

from .base import Base
from .user import gen_uuid


class Follow(Base):
    __tablename__ = "follows"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    follower_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="关注者")
    following_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="被关注者")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uk_follow"),
    )
