"""规格模板模型 - 预设规格模板"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from .base import Base
from .user import gen_uuid


class SpecificationTemplate(Base):
    """规格模板表（预设规格，如：颜色、尺寸、容量等）"""

    __tablename__ = "specification_templates"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(50), nullable=False, comment="规格名称")
    description = Column(String(200), nullable=True, comment="规格描述")
    values_json = Column(Text, nullable=False, comment="规格值列表JSON")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
