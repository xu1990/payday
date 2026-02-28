"""积分订单支付流水模型 - 混合支付系统"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base
from .user import gen_uuid


class PointPayment(Base):
    """积分订单支付流水表"""

    __tablename__ = "point_payments"

    id = Column(String(36), primary_key=True, default=gen_uuid)

    # 关联订单
    order_id = Column(
        String(36),
        ForeignKey("point_orders.id"),
        nullable=False,
        index=True,
        comment="订单ID"
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 支付信息
    out_trade_no = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="商户订单号"
    )
    transaction_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="第三方交易ID（微信）"
    )

    # 金额信息
    total_amount = Column(Integer, nullable=False, comment="支付总金额（分）")
    cash_amount = Column(Integer, nullable=False, comment="现金支付金额（分）")
    points_amount = Column(Integer, nullable=False, default=0, comment="积分支付金额")

    # 支付状态
    status = Column(
        Enum("created", "paying", "success", "failed", "closed", "refunded", name="point_payment_status"),
        default="created",
        nullable=False,
        comment="支付状态"
    )

    # 支付方式
    payment_method = Column(String(20), nullable=False, comment="支付方式: wechat")

    # 支付渠道返回信息
    prepay_id = Column(String(64), nullable=True, comment="预支付交易会话标识")
    qr_code_url = Column(String(500), nullable=True, comment="支付二维码URL")

    # 支付时间
    paid_at = Column(DateTime, nullable=True, comment="支付成功时间")
    expired_at = Column(DateTime, nullable=True, comment="支付过期时间")
    closed_at = Column(DateTime, nullable=True, comment="支付关闭时间")

    # 失败信息
    fail_code = Column(String(50), nullable=True, comment="失败错误码")
    fail_message = Column(String(255), nullable=True, comment="失败错误信息")

    # 请求/响应快照
    request_snapshot = Column(Text, nullable=True, comment="支付请求快照（JSON）")
    response_snapshot = Column(Text, nullable=True, comment="支付响应快照（JSON）")

    # 幂等性
    idempotency_key = Column(
        String(64),
        nullable=True,
        index=True,
        comment="幂等性键"
    )

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    order = relationship("PointOrder", back_populates="payments")
    notifies = relationship("PointPaymentNotify", back_populates="payment")
