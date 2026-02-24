"""积分订单模型 - Sprint 4.7 商品兑换系统"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum

from .base import Base
from .user import gen_uuid


class PointOrder(Base):
    """积分订单表（替代原PointRedemption）"""

    __tablename__ = "point_orders"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    product_id = Column(String(36), ForeignKey("point_products.id"), nullable=False, comment="商品ID")

    # 订单信息
    order_number = Column(String(32), unique=True, nullable=False, index=True, comment="订单号")
    product_name = Column(String(100), nullable=False, comment="商品名称（快照）")
    product_image = Column(String(500), nullable=True, comment="商品图片（快照）")
    points_cost = Column(Integer, nullable=False, comment="消耗积分（快照）")

    # 收货信息
    delivery_info = Column(Text, nullable=True, comment="收货信息 JSON")
    sku_id = Column(String(36), ForeignKey("point_product_skus.id"),
                   nullable=True, comment="SKU ID")
    address_id = Column(String(36), ForeignKey("user_addresses.id"),
                       nullable=True, comment="收货地址ID")
    shipment_id = Column(String(36), ForeignKey("order_shipments.id"),
                        nullable=True, comment="发货ID")
    notes = Column(Text, nullable=True, comment="备注")

    # 状态
    status = Column(
        Enum("pending", "completed", "cancelled", "refunded", name="point_order_status"),
        default="pending",
        nullable=False,
        comment="订单状态"
    )

    # 处理信息
    admin_id = Column(String(36), ForeignKey("admin_users.id"), nullable=True, comment="处理管理员ID")
    processed_at = Column(DateTime, nullable=True, comment="处理时间")
    notes_admin = Column(Text, nullable=True, comment="管理员备注")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    user = None  # relationship("User", back_populates="point_orders")
    product = None  # relationship("PointProduct", back_populates="orders")
    admin = None  # relationship("AdminUser", back_populates="processed_point_orders")
