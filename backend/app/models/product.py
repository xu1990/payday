"""
商品模型 - Enhanced E-commerce Module
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String

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


class ProductSKU(Base):
    """商品SKU（规格）表"""
    __tablename__ = "product_skus"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)

    # SKU identification
    sku_code = Column(String(50), unique=True, nullable=False, comment="SKU代码")
    name = Column(String(100), nullable=False, comment="SKU名称")

    # Variant attributes
    attributes = Column(JSON, nullable=False, comment="规格属性")

    # Inventory
    stock = Column(Integer, default=0, nullable=False, comment="库存")
    stock_unlimited = Column(Boolean, default=False, nullable=False, comment="库存无限")

    # Images (specific to this SKU)
    images = Column(JSON, nullable=True, comment="SKU图片")

    # Weight for shipping
    weight_grams = Column(Integer, nullable=True, comment="重量(克)")

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    # product = relationship("Product", back_populates="skus")


class ProductPrice(Base):
    """商品多价格表"""
    __tablename__ = "product_prices"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    sku_id = Column(String(36), ForeignKey("product_skus.id"), nullable=False, index=True)

    # Price type
    price_type = Column(
        SQLEnum("base", "member", "bulk", "promotion", name="price_type_enum"),
        nullable=False
    )

    # Price (can be points or cash)
    price_amount = Column(Integer, nullable=False, comment="价格(分或积分)")
    currency = Column(
        SQLEnum("CNY", "POINTS", name="price_currency_enum"),
        nullable=False
    )

    # Conditions
    min_quantity = Column(Integer, default=1, nullable=False, comment="最小数量")
    membership_level = Column(Integer, nullable=True, comment="会员等级")

    # Validity period
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProductBundle(Base):
    """商品套餐（组合商品）表"""
    __tablename__ = "product_bundles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    bundle_product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    component_product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    component_sku_id = Column(String(36), ForeignKey("product_skus.id"), nullable=True)
    quantity = Column(Integer, default=1, nullable=False, comment="数量")
    is_required = Column(Boolean, default=True, nullable=False, comment="是否必选")

    # Relationships
    # bundle_product = relationship("Product", foreign_keys=[bundle_product_id])
    # component_product = relationship("Product", foreign_keys=[component_product_id])
