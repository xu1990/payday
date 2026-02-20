"""
帖子表 - 与迭代规划 2.2 数据模型一致，技术方案 2.2.1 分表策略（当前先单表，后续可按 created_at 按月分表）
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, Enum, ForeignKey, JSON, func

from .base import Base
from .user import gen_uuid


class Post(Base):
    __tablename__ = "posts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    anonymous_name = Column(String(50), nullable=False, comment="发帖时用户匿名昵称冗余")
    content = Column(Text, nullable=False)
    images = Column(JSON, nullable=True, comment="图片 URL 列表，最多9张")
    tags = Column(JSON, nullable=True, comment="标签列表")
    type = Column(
        Enum("complaint", "sharing", "question", name="post_type_enum"),
        default="complaint",
        nullable=False,
    )
    salary_range = Column(String(20), nullable=True, comment="工资区间可选")
    industry = Column(String(50), nullable=True)
    city = Column(String(50), nullable=True)
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=True, index=True, comment="关联话题ID")
    visibility = Column(
        Enum("public", "followers", "private", name="post_visibility_enum"),
        default="public",
        nullable=False,
        comment="公开范围: public=公开, followers=关注者可见, private=仅自己可见"
    )

    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)

    status = Column(
        Enum("normal", "hidden", "deleted", name="post_status_enum"),
        default="normal",
        nullable=False,
    )
    risk_status = Column(
        Enum("pending", "approved", "rejected", name="risk_status_enum"),
        default="pending",
        nullable=False,
    )
    risk_score = Column(Integer, nullable=True)
    risk_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
