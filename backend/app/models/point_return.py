"""积分订单退货模型"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum

from .base import Base
from .user import gen_uuid


class PointReturn(Base):
    """积分订单退货表"""

    __tablename__ = "point_returns"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    order_id = Column(String(36), ForeignKey("point_orders.id"),
                     nullable=False, index=True, comment="订单ID")
    reason = Column(Text, nullable=False, comment="退货原因")

    status = Column(
        Enum("requested", "approved", "rejected",
             name="point_return_status"),
        default="requested",
        nullable=False,
        comment="退货状态"
    )

    admin_notes = Column(Text, nullable=True, comment="管理员备注")
    admin_id = Column(String(36), ForeignKey("admin_users.id"),
                     nullable=True, comment="处理管理员ID")

    created_at = Column(DateTime, default=datetime.utcnow,
                       nullable=False, comment="申请时间")
    processed_at = Column(DateTime, nullable=True, comment="处理时间")
