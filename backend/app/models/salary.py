"""
工资记录表 - 与技术方案 2.2.3 金额加密存储
"""
from datetime import date, datetime
from sqlalchemy import Column, String, Text, Date, Enum, DateTime, ForeignKey, JSON

from .base import Base
from .user import gen_uuid


class SalaryRecord(Base):
    __tablename__ = "salary_records"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    config_id = Column(String(36), ForeignKey("payday_configs.id"), nullable=False, index=True)
    amount_encrypted = Column(Text, nullable=False, comment="加密后的金额")
    payday_date = Column(Date, nullable=False, index=True, comment="发薪日期")
    salary_type = Column(
        Enum("normal", "bonus", "allowance", "other", name="salary_type_enum"),
        default="normal",
        nullable=False,
    )
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
