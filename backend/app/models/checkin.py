"""
打卡表 - Sprint 3.3 打卡功能 + Sprint 4.5 增强功能
"""
from datetime import date, datetime

from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Integer, String

from .base import Base
from .user import gen_uuid


class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    check_date = Column(Date, nullable=False, index=True, comment="打卡日期")
    note = Column(String(500), nullable=True, comment="打卡备注")

    # Sprint 4.5 增强字段
    checkin_type = Column(String(50), nullable=True, default="daily",
                          comment="打卡类型: daily/weekly/milestone/special")
    reward_points = Column(Integer, nullable=True, default=0, comment="奖励积分")
    streak_days = Column(Integer, nullable=True, default=0, comment="连续打卡天数")
    mood = Column(String(50), nullable=True, comment="打卡时的心情")
    tags = Column(JSON, nullable=True, comment="打卡标签 JSON")

    created_at = Column(DateTime, default=datetime.utcnow)
