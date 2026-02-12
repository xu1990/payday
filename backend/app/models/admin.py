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
    role = Column(String(20), nullable=False, default="admin", comment="角色: superadmin/admin/readonly")
    is_active = Column(String(1), nullable=False, default="1", comment="是否启用: 1=启用, 0=禁用")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
