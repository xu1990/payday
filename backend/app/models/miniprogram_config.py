"""
小程序配置表 - 管理后台配置小程序基础设置
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer

from .base import Base
from .user import gen_uuid


class MiniprogramConfig(Base):
    """小程序配置表"""
    __tablename__ = "miniprogram_configs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    key = Column(String(50), nullable=False, unique=True, comment="配置键")
    value = Column(Text, nullable=True, comment="配置值（JSON或文本）")
    description = Column(String(200), nullable=True, comment="配置说明")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
