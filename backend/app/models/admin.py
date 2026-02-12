"""
管理员表 - 管理后台账号密码登录（迭代规划 1.1 系统设置）
"""
from datetime import datetime

from sqlalchemy import Column, String, DateTime

from .base import Base
from .user import gen_uuid


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True, comment="登录名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
