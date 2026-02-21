"""
用户表 - 与技术方案 / PRD 5.1.1 一致
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Enum, DateTime
from sqlalchemy.orm import relationship

from .base import Base


def gen_uuid():
    return str(uuid.uuid4()).replace("-", "")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    openid = Column(String(64), unique=True, nullable=False, index=True, comment="微信 openid")
    unionid = Column(String(64), nullable=True, comment="微信 unionid")
    anonymous_name = Column(String(50), nullable=False, comment="匿名昵称")
    nickname = Column(String(50), nullable=True, comment="显示昵称")
    avatar = Column(String(255), nullable=True, comment="头像 URL")
    bio = Column(String(200), nullable=True, comment="个人简介")
    phone_number = Column(String(20), nullable=True, index=True, comment="手机号（加密）")
    phone_verified = Column(Integer, default=0, comment="手机号是否验证")

    follower_count = Column(Integer, default=0, comment="粉丝数")
    following_count = Column(Integer, default=0, comment="关注数")
    post_count = Column(Integer, default=0, comment="发帖数")

    allow_follow = Column(Integer, default=1, comment="允许被关注")
    allow_comment = Column(Integer, default=1, comment="允许评论")

    status = Column(
        Enum("normal", "disabled", name="user_status"),
        default="normal",
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deactivated_at = Column(DateTime, nullable=True, comment="注销时间（软删除）")

    # 关系
    phone_lookup = relationship("PhoneLookup", back_populates="user", uselist=False)
