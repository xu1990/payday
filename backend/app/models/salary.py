"""
工资记录表 - 与技术方案 2.2.3 金额加密存储；Sprint 3.3 增强字段
"""
from datetime import date, datetime
from sqlalchemy import Column, String, Text, Date, Enum, DateTime, ForeignKey, JSON, Integer, Numeric

from .base import Base
from .user import gen_uuid


class SalaryRecord(Base):
    __tablename__ = "salary_records"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    config_id = Column(String(36), ForeignKey("payday_configs.id"), nullable=False, index=True)
    amount_encrypted = Column(Text, nullable=False, comment="加密后的金额")
    encryption_salt = Column(String(44), nullable=False, comment="加密使用的盐值 (base64编码)")
    payday_date = Column(Date, nullable=False, index=True, comment="发薪日期")
    salary_type = Column(
        Enum("normal", "bonus", "allowance", "other", name="salary_type_enum"),
        default="normal",
        nullable=False,
    )
    # Sprint 3.3 增强字段
    pre_tax_amount = Column(Numeric(10, 2), nullable=True, comment="税前金额（分）")
    tax_amount = Column(Numeric(10, 2), nullable=True, comment="扣税金额（分）")
    source = Column(String(50), nullable=True, comment="来源：公司/工厂/其他")
    delayed_days = Column(Integer, nullable=True, comment="延迟天数")
    images = Column(JSON, nullable=True, comment="工资条图片 URLs")
    note = Column(Text, nullable=True)
    mood = Column(
        Enum("happy", "relief", "sad", "angry", "expect", name="mood_enum"),
        nullable=False,
    )

    risk_status = Column(
        Enum("pending", "approved", "rejected", name="risk_status_enum"),
        default="pending",
        nullable=False,
        comment="风控状态",
    )
    risk_check_time = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
