"""
风险预警表 - Sprint 3.5 运营功能
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey

from .base import Base
from .user import gen_uuid


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    target_type = Column(String(20), nullable=False, comment="目标类型：post/comment")
    target_id = Column(String(36), nullable=False, comment="目标ID")
    risk_score = Column(Integer, nullable=False, comment="风险评分（0-100）")
    risk_reason = Column(String(200), nullable=True, comment="风险原因")
    is_handled = Column(Boolean, default=False, nullable=False, comment="是否已处理")
    handled_by = Column(String(36), ForeignKey("users.id"), nullable=True, comment="处理人ID")
    handled_at = Column(DateTime, nullable=True, comment="处理时间")
    created_at = Column(DateTime, default=datetime.utcnow)
