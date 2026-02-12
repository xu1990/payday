"""
会员与订单表 - Sprint 3.5 会员与商业化
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, Text, Enum, Boolean

from .base import Base
from .user import gen_uuid


class Membership(Base):
    """会员套餐表"""
    __tablename__ = "memberships"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(50), nullable=False, comment="套餐名称")
    description = Column(Text, nullable=True, comment="权益说明")
    price = Column(Numeric(10, 2), nullable=False, comment="月费（分）")
    duration_days = Column(Integer, nullable=False, comment="有效期（天数）")
    is_active = Column(Integer, default=1, nullable=False, comment="是否启用")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    created_at = Column(DateTime, default=datetime.utcnow)


class MembershipOrder(Base):
    """会员订单表"""
    __tablename__ = "membership_orders"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    membership_id = Column(String(36), ForeignKey("memberships.id"), nullable=False, comment="套餐ID")
    amount = Column(Numeric(10, 2), nullable=False, comment="实付金额（分）")
    status = Column(
        Enum("pending", "paid", "cancelled", "refunded", name="order_status_enum"),
        default="pending",
        nullable=False,
    )
    payment_method = Column(String(20), nullable=True, comment="支付方式：wechat/alipay")
    transaction_id = Column(String(100), nullable=True, comment="第三方交易ID")
    start_date = Column(DateTime, nullable=False, comment="会员开始日期")
    end_date = Column(DateTime, nullable=True, comment="会员到期日期")
    auto_renew = Column(Integer, default=0, nullable=False, comment="是否自动续费")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppTheme(Base):
    """主题配置表"""
    __tablename__ = "app_themes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(50), nullable=False, comment="主题名称")
    code = Column(String(50), nullable=False, unique=True, comment="主题代码")
    preview_image = Column(String(500), nullable=True, comment="预览图")
    config = Column(Text, nullable=True, comment="主题配置（JSON）")
    is_premium = Column(Boolean, default=False, nullable=False, comment="是否会员专属")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
