"""Ability Points Models - 能力值系统（Sprint 4.6）"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Numeric

from app.models.base import Base
from app.models.user import gen_uuid


class AbilityPoint(Base):
    """用户能力值积分表"""

    __tablename__ = "ability_points"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True, comment="用户ID")

    # 积分与等级
    total_points = Column(Integer, nullable=False, default=0, comment="总积分")
    available_points = Column(Integer, nullable=False, default=0, comment="可用积分（未兑换的）")
    level = Column(Integer, nullable=False, default=1, comment="等级")

    # 统计
    total_earned = Column(Integer, nullable=False, default=0, comment="累计获得积分")
    total_spent = Column(Integer, nullable=False, default=0, comment="累计消费积分")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # 关系
    user = None  # relationship("User", back_populates="ability_points")


class AbilityPointTransaction(Base):
    """积分流水记录"""

    __tablename__ = "ability_point_transactions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")

    # 交易信息
    amount = Column(Integer, nullable=False, comment="积分变动（正数为获得，负数为消费）")
    balance_after = Column(Integer, nullable=False, comment="变动后余额")

    # 交易类型
    transaction_type = Column(String(50), nullable=False, comment="类型: checkin/post/like/redeem/etc.")
    event_type = Column(String(50), nullable=True, comment="事件类型（用于hooks系统）")

    # 关联信息
    reference_id = Column(String(36), nullable=True, comment="关联记录ID（如帖子ID、打卡ID等）")
    reference_type = Column(String(50), nullable=True, comment="关联记录类型")

    # 描述
    description = Column(String(200), nullable=True, comment="交易描述")
    metadata = Column(Text, nullable=True, comment="额外信息 JSON")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")

    # 关系
    user = None  # relationship("User", back_populates="point_transactions")


class PointRedemption(Base):
    """积分兑换记录"""

    __tablename__ = "point_redemptions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")

    # 兑换信息
    reward_name = Column(String(100), nullable=False, comment="奖励名称")
    reward_type = Column(String(50), nullable=False, comment="奖励类型: coupon/gift/vip/etc.")
    points_cost = Column(Integer, nullable=False, comment="消耗积分")

    # 状态
    status = Column(String(50), nullable=False, default="pending", comment="状态: pending/approved/completed/rejected")

    # 兑换详情
    delivery_info = Column(Text, nullable=True, comment="配送信息 JSON")
    notes = Column(Text, nullable=True, comment="备注")

    # 审核信息（管理员）
    admin_id = Column(String(36), ForeignKey("admin_users.id"), nullable=True, comment="审核管理员ID")
    processed_at = Column(DateTime, nullable=True, comment="处理时间")
    rejection_reason = Column(String(200), nullable=True, comment="拒绝原因")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # 关系
    user = None  # relationship("User", back_populates="redemptions")
    admin = None  # relationship("AdminUser", back_populates="processed_redemptions")
