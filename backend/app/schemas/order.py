"""
订单 - 请求/响应模型
E-commerce Order System - Unified order schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class OrderItemCreate(BaseModel):
    """订单明细创建（添加商品到订单）"""
    sku_id: str = Field(..., description="SKU ID")
    quantity: int = Field(..., ge=1, description="数量，必须大于等于1")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """验证数量必须大于等于1"""
        if v < 1:
            raise ValueError("quantity must be at least 1")
        return v


class OrderItemResponse(BaseModel):
    """订单明细响应"""
    id: str
    order_id: str
    product_id: str
    sku_id: Optional[str] = None
    product_name: str
    sku_name: Optional[str] = None
    product_image: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    unit_price: str  # Numeric as string for precision
    quantity: int
    subtotal: str
    bundle_components: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """订单创建（下单）"""
    items: List[OrderItemCreate] = Field(..., min_length=1, description="订单明细列表，至少包含一项")
    shipping_address_id: str = Field(..., description="收货地址ID")
    payment_method: Literal["wechat", "alipay", "points", "hybrid"] = Field(
        ..., description="支付方式"
    )
    points_to_use: int = Field(0, ge=0, description="使用的积分数量")


class OrderResponse(BaseModel):
    """订单响应"""
    id: str
    user_id: str
    order_number: str
    total_amount: str
    points_used: int
    discount_amount: str
    shipping_cost: str
    final_amount: str
    payment_method: str
    payment_status: str
    transaction_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    status: str
    shipping_address_id: Optional[str] = None
    shipping_template_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    shipping_address: Optional[Any] = None

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    """订单更新"""
    status: Optional[Literal[
        "pending", "paid", "processing", "shipped",
        "delivered", "completed", "cancelled", "refunding", "refunded"
    ]] = None
    shipping_address_id: Optional[str] = None
