"""
物流模型 - Shipping Module
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Numeric

from .base import Base
from .user import gen_uuid


class ShippingTemplate(Base):
    """运费模板表"""
    __tablename__ = "shipping_templates"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(String(200), nullable=True, comment="模板描述")

    # Pricing type
    charge_type = Column(
        String(20),
        nullable=False,
        comment="计费方式: weight/quantity/fixed"
    )

    # Default shipping (for regions not specified)
    default_first_unit = Column(Integer, nullable=False, comment="首件/首重(克或件)")
    default_first_cost = Column(Integer, nullable=False, comment="首件运费(分)")
    default_continue_unit = Column(Integer, nullable=False, comment="续件/续重(克或件)")
    default_continue_cost = Column(Integer, nullable=False, comment="续件运费(分)")

    # Free shipping threshold
    free_threshold = Column(Integer, nullable=True, comment="包邮门槛(分)")

    # Estimated delivery
    estimate_days_min = Column(Integer, nullable=True, comment="预计到达最少天数")
    estimate_days_max = Column(Integer, nullable=True, comment="预计到达最多天数")

    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    # regions = relationship("ShippingTemplateRegion", back_populates="template")


class ShippingTemplateRegion(Base):
    """运费模板区域配置表"""
    __tablename__ = "shipping_template_regions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    template_id = Column(String(36), ForeignKey("shipping_templates.id"), nullable=False, index=True)

    # Region designation
    region_codes = Column(String(500), nullable=False, comment="区域代码列表(逗号分隔)")
    region_names = Column(String(500), nullable=False, comment="区域名称列表(逗号分隔)")

    # Regional pricing
    first_unit = Column(Integer, nullable=False, comment="首件/首重")
    first_cost = Column(Integer, nullable=False, comment="首件运费(分)")
    continue_unit = Column(Integer, nullable=False, comment="续件/续重")
    continue_cost = Column(Integer, nullable=False, comment="续件运费(分)")

    # Free shipping for this region
    free_threshold = Column(Integer, nullable=True, comment="包邮门槛(分)")

    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    # template = relationship("ShippingTemplate", back_populates="regions")


class CourierCompany(Base):
    """物流公司表"""
    __tablename__ = "courier_companies"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    code = Column(String(50), unique=True, nullable=False, comment="物流公司代码")
    name = Column(String(100), nullable=False, comment="物流公司名称")
    website = Column(String(200), nullable=True, comment="官网")
    tracking_url = Column(String(200), nullable=True, comment="物流查询URL")

    # Service capabilities
    supports_cod = Column(Boolean, default=False, nullable=False, comment="支持货到付款")
    supports_cold_chain = Column(Boolean, default=False, nullable=False, comment="支持冷链")

    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    # shipments = relationship("OrderShipment", back_populates="courier")
