"""
每月支出明细 Model - 记录每月工资的花销明细
形成「收入-支出-结余」的完整财务闭环
"""
from datetime import datetime

from app.models.base import Base
from app.models.user import gen_uuid
from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.mysql import NUMERIC


class ExpenseRecord(Base):
    """支出记录模型"""

    __tablename__ = "expense_records"

    id = Column(String(36), primary_key=True, default=gen_uuid, comment="主键ID")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    salary_record_id = Column(String(36), ForeignKey("salary_records.id"), nullable=False, index=True, comment="工资记录ID")

    # 支出信息
    expense_date = Column(Date, nullable=False, index=True, comment="支出日期")
    category = Column(String(50), nullable=False, index=True, comment="支出分类")
    subcategory = Column(String(50), nullable=True, comment="子分类")
    amount = Column(Numeric(10, 2), nullable=False, comment="支出金额")
    note = Column(Text, nullable=True, comment="备注")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # 关系
    user = None  # relationship("User", back_populates="expense_records")
    salary_record = None  # relationship("SalaryRecord", back_populates="expense_records")

    # 索引
    __table_args__ = (
        Index('idx_expense_user_date', 'user_id', 'expense_date'),
    )
