"""
敏感词表 - 用于风控审核
"""
from sqlalchemy import Column, String, Boolean
from datetime import datetime

from .base import Base


class SensitiveWord(Base):
    """敏感词模型"""
    __tablename__ = "sensitive_words"

    id = Column(String(36), primary_key=True, comment="敏感词ID")
    word = Column(String(100), nullable=False, unique=True, index=True, comment="敏感词")
    category = Column(String(50), nullable=False, comment="分类：illegal|porn|violence|politics|fraud|other")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
