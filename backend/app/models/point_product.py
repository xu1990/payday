"""积分商品模型 - Sprint 4.7 商品兑换系统"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime

from .base import Base
from .user import gen_uuid


class PointProduct(Base):
    """积分商品表"""

    __tablename__ = "point_products"

    id = Column(String(36), primary_key=True, default=gen_uuid)

    # 基本信息
    name = Column(String(100), nullable=False, comment="商品名称")
    description = Column(Text, nullable=True, comment="商品描述")
    image_urls = Column(Text, nullable=True, comment="商品图片URLs (JSON数组)")

    # 价格与库存
    points_cost = Column(Integer, nullable=False, comment="积分价格")
    stock = Column(Integer, nullable=False, default=0, comment="库存数量")
    stock_unlimited = Column(Boolean, default=False, nullable=False, comment="库存无限")

    # 分类与排序
    category = Column(String(50), nullable=True, comment="商品分类")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重（越大越靠前）")

    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否上架")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    orders = None  # relationship("PointOrder", back_populates="product")
