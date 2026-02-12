"""
发薪日配置表 - 与技术方案 / PRD 5.1.2 一致
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Enum, DateTime, ForeignKey

from .base import Base
from .user import gen_uuid


class PaydayConfig(Base):
    __tablename__ = "payday_configs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    job_name = Column(String(50), nullable=False, comment="工作名称")
    payday = Column(Integer, nullable=False, comment="发薪日 1-31")
    calendar_type = Column(
        Enum("solar", "lunar", name="calendar_type_enum"),
        default="solar",
        nullable=False,
    )
    estimated_salary = Column(Integer, nullable=True, comment="预估工资（分）")
    is_active = Column(Integer, default=1, nullable=False, comment="是否启用")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
