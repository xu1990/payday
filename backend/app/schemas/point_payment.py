"""积分订单支付Schema - 混合支付系统"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PointPaymentStatus(str, Enum):
    """支付状态枚举"""
    CREATED = "created"
    PAYING = "paying"
    SUCCESS = "success"
    FAILED = "failed"
    CLOSED = "closed"
    REFUNDED = "refunded"


class NotifyProcessStatus(str, Enum):
    """回调处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class CreatePaymentRequest(BaseModel):
    """创建支付请求"""
    order_id: str = Field(..., description="订单ID")
    idempotency_key: Optional[str] = Field(None, description="幂等性键（防重复提交）")


class PaymentParams(BaseModel):
    """小程序支付参数"""
    timeStamp: str = Field(..., description="时间戳")
    nonceStr: str = Field(..., description="随机字符串")
    package: str = Field(..., description="订单详情")
    signType: str = Field(..., description="签名方式")
    paySign: str = Field(..., description="签名")


class CreatePaymentResponse(BaseModel):
    """创建支付响应"""
    success: bool = Field(..., description="是否成功")
    payment_id: str = Field(..., description="支付ID")
    out_trade_no: str = Field(..., description="商户订单号")
    cash_amount: int = Field(..., description="支付金额（分）")
    points_amount: int = Field(0, description="积分支付金额")
    payment_params: Optional[PaymentParams] = Field(None, description="小程序支付参数")
    message: Optional[str] = Field(None, description="消息")


class PaymentStatusResponse(BaseModel):
    """支付状态响应"""
    payment_id: str
    order_id: str
    out_trade_no: str
    status: PointPaymentStatus
    cash_amount: int
    points_amount: int = 0
    payment_method: str
    transaction_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    fail_code: Optional[str] = None
    fail_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PointPaymentResponse(BaseModel):
    """支付流水响应"""
    id: str
    order_id: str
    user_id: str
    out_trade_no: str
    transaction_id: Optional[str] = None
    total_amount: int
    cash_amount: int
    points_amount: int = 0
    status: PointPaymentStatus
    payment_method: str
    prepay_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    fail_code: Optional[str] = None
    fail_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PointPaymentNotifyResponse(BaseModel):
    """支付回调响应"""
    id: str
    payment_id: Optional[str] = None
    transaction_id: Optional[str] = None
    out_trade_no: Optional[str] = None
    notify_type: str
    process_status: NotifyProcessStatus
    process_message: Optional[str] = None
    process_attempts: int = 0
    notified_at: datetime
    processed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderCreateResponse(BaseModel):
    """创建订单响应（增强版）"""
    success: bool
    order_id: str
    order_number: str
    payment_mode: str
    points_cost: int
    cash_amount: Optional[int] = None
    need_payment: bool = Field(..., description="是否需要支付（纯积分时为false）")
    payment_id: Optional[str] = Field(None, description="支付ID（需要支付时返回）")
    message: Optional[str] = None
