"""支付回调通知模型 - 混合支付系统"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base
from .user import gen_uuid


class PointPaymentNotify(Base):
    """支付回调通知表"""

    __tablename__ = "point_payment_notifies"

    id = Column(String(36), primary_key=True, default=gen_uuid)

    # 关联支付
    payment_id = Column(
        String(36),
        ForeignKey("point_payments.id"),
        nullable=True,
        index=True,
        comment="支付ID"
    )

    # 回调信息
    transaction_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="第三方交易ID"
    )
    out_trade_no = Column(
        String(64),
        nullable=True,
        index=True,
        comment="商户订单号"
    )

    # 回调类型
    notify_type = Column(
        String(20),
        nullable=False,
        comment="回调类型: payment, refund, close"
    )

    # 原始数据
    raw_data = Column(Text, nullable=False, comment="原始回调数据")
    parsed_data = Column(Text, nullable=True, comment="解析后的数据（JSON）")

    # 处理状态
    process_status = Column(
        Enum("pending", "processing", "success", "failed", name="notify_process_status"),
        default="pending",
        nullable=False,
        comment="处理状态"
    )
    process_message = Column(String(255), nullable=True, comment="处理信息")
    process_attempts = Column(Integer, default=0, nullable=False, comment="处理尝试次数")

    # 时间戳
    notified_at = Column(DateTime, nullable=False, comment="回调通知时间")
    processed_at = Column(DateTime, nullable=True, comment="处理完成时间")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    payment = relationship("PointPayment", back_populates="notifies")
