"""
物流跟踪模型 - Tracking Module
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum

from .base import Base
from .user import gen_uuid


class TrackingStatus:
    """物流跟踪状态常量"""
    PENDING = "pending"  # 待发货
    SHIPPED = "shipped"  # 已发货
    IN_TRANSIT = "in_transit"  # 运输中
    OUT_FOR_DELIVERY = "out_for_delivery"  # 派送中
    DELIVERED = "delivered"  # 已签收
    FAILED = "failed"  # 派送失败
    RETURNED = "returned"  # 已退回
    EXCEPTION = "exception"  # 异常


class Shipment(Base):
    """物流跟踪表"""
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="物流ID")
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True, comment="订单ID")

    # Courier information
    courier_code = Column(String(20), nullable=False, comment="物流公司代码")
    courier_name = Column(String(50), nullable=False, comment="物流公司名称")
    tracking_number = Column(String(50), nullable=False, unique=True, index=True, comment="物流单号")

    # Shipment status
    status = Column(
        String(20),
        default=TrackingStatus.PENDING,
        nullable=False,
        index=True,
        comment="发货状态"
    )

    # Timestamps
    shipped_at = Column(DateTime, nullable=True, comment="发货时间")
    delivered_at = Column(DateTime, nullable=True, comment="签收时间")
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="最后更新时间")

    # Estimated delivery
    estimated_delivery = Column(DateTime, nullable=True, comment="预计送达时间")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # Relationships
    # order = relationship("Order", back_populates="shipments")
    # events = relationship("TrackingEvent", back_populates="shipment", cascade="all, delete-orphan")


class TrackingEvent(Base):
    """物流跟踪事件表"""
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="事件ID")
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True, comment="物流ID")

    # Event information
    status = Column(String(50), nullable=False, comment="事件状态")
    description = Column(String(500), nullable=False, comment="事件描述")
    location = Column(String(200), nullable=True, comment="事件地点")

    # Timestamp
    timestamp = Column(DateTime, nullable=False, index=True, comment="事件时间")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")

    # Relationships
    # shipment = relationship("Shipment", back_populates="events")
