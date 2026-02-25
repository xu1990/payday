"""积分商品SKU模型 - 多规格系统"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from .base import Base
from .user import gen_uuid


class PointSpecification(Base):
    """商品规格定义表（如：颜色、尺寸）"""

    __tablename__ = "point_specifications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(String(36), ForeignKey("point_products.id"),
                       nullable=False, index=True, comment="商品ID")
    name = Column(String(50), nullable=False, comment="规格名称")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PointSpecificationValue(Base):
    """规格值表（如：红色、蓝色、L、XL）"""

    __tablename__ = "point_specification_values"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    specification_id = Column(String(36), ForeignKey("point_specifications.id"),
                             nullable=False, index=True, comment="规格ID")
    value = Column(String(50), nullable=False, comment="规格值")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PointProductSKU(Base):
    """商品SKU表 - 多规格库存管理"""

    __tablename__ = "point_product_skus"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(String(36), ForeignKey("point_products.id"),
                       nullable=False, index=True, comment="商品ID")
    sku_code = Column(String(50), unique=True, nullable=False,
                     index=True, comment="SKU编码")
    specs = Column(Text, nullable=False, comment="规格组合JSON")

    # SKU独立库存和价格
    stock = Column(Integer, default=0, nullable=False, comment="库存数量")
    stock_unlimited = Column(Boolean, default=False,
                             nullable=False, comment="库存无限")
    points_cost = Column(Integer, nullable=False, comment="积分价格")
    image_url = Column(String(500), nullable=True, comment="SKU专属图片")

    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
