"""积分商品分类模型"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from .base import Base
from .user import gen_uuid


class PointCategory(Base):
    """积分商品分类表 - 支持多级层级"""

    __tablename__ = "point_categories"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(50), nullable=False, comment="分类名称")
    description = Column(Text, nullable=True, comment="分类描述")
    parent_id = Column(String(36), ForeignKey("point_categories.id"),
                       nullable=True, index=True, comment="父分类ID")
    icon_url = Column(String(500), nullable=True, comment="分类图标URL")
    banner_url = Column(String(500), nullable=True, comment="分类横幅URL")
    level = Column(Integer, nullable=False, comment="层级(1/2/3)")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
