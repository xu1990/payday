"""
支付相关的 Pydantic schemas
"""
from pydantic import BaseModel


class CreatePaymentRequest(BaseModel):
    """创建支付请求"""

    order_id: str


class PaymentParams(BaseModel):
    """小程序支付参数"""

    timeStamp: str
    nonceStr: str
    package: str
    signType: str
    paySign: str
    out_trade_no: str


class CreatePaymentResponse(BaseModel):
    """创建支付响应"""

    success: bool
    data: PaymentParams | None = None
    message: str


class PaymentErrorResponse(BaseModel):
    """支付错误响应"""

    success: bool
    message: str
