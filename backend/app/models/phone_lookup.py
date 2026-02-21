"""
手机号查找表 - 用于高效的用户手机号查询
使用SHA-256哈希存储手机号，保护隐私同时提供快速查询
"""
import hashlib
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .user import gen_uuid


class PhoneLookup(Base):
    """手机号查找表 - 用于快速根据手机号查找用户"""

    __tablename__ = "phone_lookup"

    id = Column(String(36), primary_key=True, default=gen_uuid, comment="主键ID")

    # 手机号的SHA-256哈希值（隐私保护）
    phone_hash = Column(String(64), nullable=False, unique=True, index=True, comment="手机号SHA-256哈希")

    # 关联的用户ID
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")

    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")

    # 更新时间（手机号变更时更新）
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )

    # 关系（使用 passive_deletes 确保数据库级 CASCADE 生效）
    user = relationship("User", back_populates="phone_lookup", passive_deletes='all')

    # 索引
    __table_args__ = (
        Index('idx_phone_lookup_hash', 'phone_hash'),
        Index('idx_phone_lookup_user_id', 'user_id'),
    )


def hash_phone_number(phone: str) -> str:
    """
    计算手机号的SHA-256哈希值

    Args:
        phone: 手机号（明文）

    Returns:
        SHA-256哈希值（十六进制字符串）
    """
    # 使用SHA-256哈希手机号
    return hashlib.sha256(phone.encode('utf-8')).hexdigest()
