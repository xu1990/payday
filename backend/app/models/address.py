"""
地址模型 - Address Management Module
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text

from .base import Base
from .user import gen_uuid


class AdminRegion(Base):
    """行政区域表（省/市/区）"""
    __tablename__ = "admin_regions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="区域代码")
    name = Column(String(50), nullable=False, comment="区域名称")
    level = Column(
        String(10),
        nullable=False,
        comment="级别: province/city/district"
    )
    parent_code = Column(String(20), ForeignKey("admin_regions.code"), nullable=True, index=True)
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    # parent = relationship("AdminRegion", remote_side=[code], backref="children")
    # addresses = relationship("UserAddress", back_populates="region")


class UserAddress(Base):
    """用户收货地址表"""
    __tablename__ = "user_addresses"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")

    # Region info (denormalized for performance)
    province_code = Column(String(20), nullable=False, comment="省份代码")
    province_name = Column(String(50), nullable=False, comment="省份名称")
    city_code = Column(String(20), nullable=False, comment="城市代码")
    city_name = Column(String(50), nullable=False, comment="城市名称")
    district_code = Column(String(20), nullable=False, comment="区县代码")
    district_name = Column(String(50), nullable=False, comment="区县名称")

    # Detailed address
    detailed_address = Column(String(200), nullable=False, comment="详细地址")
    postal_code = Column(String(10), nullable=True, comment="邮政编码")

    # Contact info
    contact_name = Column(String(50), nullable=False, comment="联系人姓名")
    contact_phone = Column(String(20), nullable=False, comment="联系电话")

    # Flags
    is_default = Column(Boolean, default=False, nullable=False, comment="是否默认地址")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否有效")

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    # user = relationship("User", back_populates="addresses")
    # region = relationship("AdminRegion", back_populates="addresses")
