"""Savings Goal Model - 存款目标（Sprint 4.4）"""
from datetime import date, datetime

from app.models.base import Base
from app.models.user import gen_uuid
from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text


class SavingsGoal(Base):
    """存款目标模型"""

    __tablename__ = "savings_goals"

    id = Column(String(36), primary_key=True, default=gen_uuid, comment="主键ID")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")

    # 目标信息
    title = Column(String(100), nullable=False, comment="目标标题")
    description = Column(Text, nullable=True, comment="目标描述")
    target_amount = Column(Numeric(10, 2), nullable=False, comment="目标金额")
    current_amount = Column(Numeric(10, 2), nullable=False, default=0, comment="当前已存金额")

    # 时间设置
    deadline = Column(Date, nullable=True, comment="目标截止日期")
    start_date = Column(Date, nullable=True, comment="目标开始日期")

    # 状态
    status = Column(
        Enum("active", "completed", "cancelled", "paused", name="savings_goal_status"),
        default="active",
        nullable=False,
        comment="目标状态"
    )

    # 分类/标签
    category = Column(String(50), nullable=True, comment="目标分类（如：买房、买车、旅游等）")
    icon = Column(String(50), nullable=True, comment="图标")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 关系
    user = None  # relationship("User", back_populates="savings_goals")
