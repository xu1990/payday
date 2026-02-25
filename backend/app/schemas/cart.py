"""
购物车 - 请求/响应模型
Shopping Cart schemas for e-commerce
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ProductBasicInfo(BaseModel):
    """商品基础信息"""
    id: str
    name: str
    description: Optional[str] = None
    images: Optional[List[str]] = None
    product_type: str
    item_type: str
    is_active: bool

    class Config:
        from_attributes = True


class SKUBasicInfo(BaseModel):
    """SKU基础信息"""
    id: str
    sku_code: str
    name: str
    attributes: Dict[str, Any]
    stock: int
    price: float
    currency: str

    class Config:
        from_attributes = True


class CartItemCreate(BaseModel):
    """购物车项创建（添加商品到购物车）"""
    sku_id: str = Field(..., description="SKU ID")
    quantity: int = Field(..., ge=1, description="数量，必须大于等于1")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """验证数量必须大于等于1"""
        if v < 1:
            raise ValueError("quantity must be at least 1")
        return v


class CartItemUpdate(BaseModel):
    """购物车项更新（修改数量）"""
    quantity: int = Field(..., ge=1, description="数量，必须大于等于1")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """验证数量必须大于等于1"""
        if v < 1:
            raise ValueError("quantity must be at least 1")
        return v


class CartItemResponse(BaseModel):
    """购物车项响应"""
    id: str
    sku_id: str
    quantity: int
    product: ProductBasicInfo
    sku: SKUBasicInfo

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    """购物车响应（完整购物车）"""
    items: List[CartItemResponse]
    total_amount: int = Field(..., description="总金额（分/积分）")
    total_points: int = Field(..., description="总积分")
    item_count: int = Field(..., description="商品总件数")
