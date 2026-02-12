"""
点赞表 - 与迭代规划 2.2 数据模型一致，target_type 区分 post/comment
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, UniqueConstraint

from .base import Base
from .user import gen_uuid


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_like_user_target"),
    )

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    target_type = Column(
        Enum("post", "comment", name="like_target_type_enum"),
        nullable=False,
    )
    target_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
