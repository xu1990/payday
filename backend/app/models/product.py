"""
商品模型 - Enhanced E-commerce Module
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON

from .base import Base
from .user import gen_uuid


class ProductCategory(Base):
    """商品分类表"""
    __tablename__ = "product_categories"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(50), nullable=False, comment="分类名称")
    code = Column(String(50), unique=True, nullable=False, comment="分类代码")
    parent_id = Column(String(36), ForeignKey("product_categories.id"), nullable=True, index=True)
    icon = Column(String(200), nullable=True, comment="图标URL")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    # parent = relationship("ProductCategory", remote_side=[id], backref="children")


class Product(Base):
    """统一商品表（替代PointProduct）"""
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=gen_uuid)

    # Basic info
    name = Column(String(100), nullable=False, comment="商品名称")
    description = Column(String(2000), nullable=True, comment="商品描述")
    images = Column(JSON, nullable=True, comment="商品图片URLs")

    # Classification
    category_id = Column(String(36), ForeignKey("product_categories.id"), nullable=True, index=True)
    product_type = Column(
        SQLEnum("point", "cash", "hybrid", name="product_type_enum"),
        default="point",
        nullable=False
    )
    item_type = Column(
        SQLEnum("physical", "virtual", "bundle", name="item_type_enum"),
        nullable=False
    )
    bundle_type = Column(
        SQLEnum("pre_configured", "custom_builder", name="bundle_type_enum"),
        nullable=True
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_virtual = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # SEO
    seo_keywords = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
