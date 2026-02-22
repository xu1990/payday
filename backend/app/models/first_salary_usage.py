"""
第一笔工资用途 Model - 用于记录用户第一笔工资的使用去向
打造职场人的"第一次"仪式感
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import NUMERIC

from app.models.base import Base
from app.models.user import gen_uuid


class FirstSalaryUsage(Base):
    """第一笔工资用途模型"""

    __tablename__ = "first_salary_usage_records"

    id = Column(String(36), primary_key=True, default=gen_uuid, comment="主键ID")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    salary_record_id = Column(String(36), ForeignKey("salary_records.id"), nullable=False, index=True, comment="工资记录ID")

    # 用途分类（预设分类，如：存起来、交家里、买东西等）
    usage_category = Column(String(50), nullable=False, comment="用途分类")
    # 子分类（可选，如：银行存款、给父母、数码产品等）
    usage_subcategory = Column(String(50), nullable=True, comment="子分类")

    # 金额（不加密，因为是用户主动分享的内容）
    amount = Column(Numeric(10, 2), nullable=False, comment="用途金额")

    # 备注
    note = Column(Text, nullable=True, comment="备注")

    # 标记为第一笔工资用途
    is_first_salary = Column(Integer, default=1, nullable=False, comment="是否为第一笔工资")

    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")

    # 关系
    user = None  # relationship("User", back_populates="first_salary_usages")
    salary_record = None  # relationship("SalaryRecord", back_populates="first_salary_usages")
