"""
打卡表 - Sprint 3.3 打卡功能
"""
from datetime import date, datetime
from sqlalchemy import Column, String, Date, DateTime, ForeignKey

from .base import Base
from .user import gen_uuid


class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    check_date = Column(Date, nullable=False, index=True, comment="打卡日期")
    note = Column(String(500), nullable=True, comment="打卡备注")
    created_at = Column(DateTime, default=datetime.utcnow)
