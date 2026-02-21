"""
薪资使用记录 Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class SalaryUsageRecord(Base):
    """薪资使用记录表"""

    __tablename__ = "salary_usage_records"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")

    # 用户关联
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 关联薪资记录
    salary_record_id = Column(
        String(36),
        ForeignKey("salary_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="薪资记录ID"
    )

    # 使用类型 (支出类型)
    usage_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="使用类型: housing/food/transport/shopping/entertainment/medical/education/other"
    )

    # 使用金额 (加密存储)
    amount = Column(String(100), nullable=False, comment="使用金额（加密）")

    # 使用日期
    usage_date = Column(DateTime, nullable=False, index=True, comment="使用日期")

    # 备注说明
    description = Column(Text, nullable=True, comment="备注说明")

    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")

    # 更新时间
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )

    # 关系 (back_populates将在后续任务中添加到User和SalaryRecord模型)
    user = relationship("User")
    salary_record = relationship("SalaryRecord")
