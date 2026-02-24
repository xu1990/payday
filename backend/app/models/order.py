"""
订单模型 - E-commerce Order System
Unified order table for all product types (point, cash, hybrid)
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum as SQLEnum, JSON

from .base import Base
from .user import gen_uuid


class Order(Base):
    """统一订单表（替代PointOrder）"""
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    order_number = Column(String(32), unique=True, nullable=False, index=True)

    # Order info
    total_amount = Column(Numeric(10, 2), nullable=False, comment="Total amount in fen/cents")
    points_used = Column(Integer, default=0, comment="Points used")
    discount_amount = Column(Numeric(10, 2), default=0, comment="Discount amount in fen/cents")
    shipping_cost = Column(Numeric(10, 2), default=0, comment="Shipping cost in fen/cents")
    final_amount = Column(Numeric(10, 2), nullable=False, comment="Final amount in fen/cents")

    # Payment
    payment_method = Column(
        SQLEnum("wechat", "alipay", "points", "hybrid", name="order_payment_method"),
        nullable=False
    )
    payment_status = Column(
        SQLEnum("pending", "paid", "failed", "refunded", name="order_payment_status"),
        default="pending"
    )
    transaction_id = Column(String(100), nullable=True, comment="Payment transaction ID")
    paid_at = Column(DateTime, nullable=True, comment="Payment timestamp")

    # Status
    status = Column(
        SQLEnum(
            "pending", "paid", "processing", "shipped",
            "delivered", "completed", "cancelled", "refunding", "refunded",
            name="order_status"
        ),
        default="pending",
        index=True
    )

    # Shipping
    shipping_address_id = Column(String(36), ForeignKey("user_addresses.id"), nullable=True)
    shipping_template_id = Column(String(36), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    # user = relationship("User", back_populates="orders")
    # shipping_address = relationship("UserAddress")
    # items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    # shipment = relationship("OrderShipment", back_populates="order", uselist=False)


class OrderItem(Base):
    """订单明细表"""
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), nullable=False, index=True)
    sku_id = Column(String(36), nullable=True)

    # Item snapshot (at time of order)
    product_name = Column(String(100), nullable=False, comment="Product name snapshot")
    sku_name = Column(String(100), nullable=True, comment="SKU name snapshot")
    product_image = Column(String(500), nullable=True, comment="Product image URL")
    attributes = Column(JSON, nullable=True, comment="SKU attributes snapshot")

    # Pricing snapshot
    unit_price = Column(Numeric(10, 2), nullable=False, comment="Unit price in fen/cents")
    quantity = Column(Integer, nullable=False, comment="Quantity")
    subtotal = Column(Numeric(10, 2), nullable=False, comment="Subtotal in fen/cents")

    # For bundles
    bundle_components = Column(JSON, nullable=True, comment="Bundle components snapshot")

    # Relationships
    # order = relationship("Order", back_populates="items")
