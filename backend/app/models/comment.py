"""
评论表 - 与迭代规划 2.2 数据模型一致，技术方案 2.2.1 按 post_id 哈希分表（当前先单表）
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Enum, ForeignKey

from .base import Base
from .user import gen_uuid


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    post_id = Column(String(36), ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    anonymous_name = Column(String(50), nullable=False, comment="评论时用户匿名昵称冗余")
    content = Column(Text, nullable=False)
    parent_id = Column(String(36), nullable=True, index=True, comment="二级回复时指向父评论 id")
    like_count = Column(Integer, default=0, nullable=False)
    risk_status = Column(
        Enum("pending", "approved", "rejected", name="risk_status_enum"),
        default="pending",
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
