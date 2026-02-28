"""积分商品Schema - Sprint 4.7 商品兑换系统"""
import json
from datetime import datetime
from typing import List, Optional

from app.models.point_product import PointProduct
from pydantic import BaseModel, Field, field_validator


class PointProductBase(BaseModel):
    """商品基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="商品名称")
    description: Optional[str] = Field(None, description="商品描述")
    points_cost: int = Field(..., gt=0, description="积分价格")

    # 支付模式（新增）
    payment_mode: str = Field("points_only", description="支付模式: points_only=纯积分, cash_only=纯现金, mixed=混合支付")
    cash_price: Optional[int] = Field(None, ge=0, description="现金价格（分）- 纯现金模式")
    mixed_points_cost: Optional[int] = Field(None, ge=0, description="混合支付时的积分价格")
    mixed_cash_price: Optional[int] = Field(None, ge=0, description="混合支付时的现金价格（分）")

    stock: int = Field(..., ge=0, description="库存数量")
    stock_unlimited: bool = Field(False, description="库存无限")
    category: Optional[str] = Field(None, description="商品分类")
    sort_order: int = Field(0, ge=0, description="排序权重")
    has_sku: bool = Field(False, description="是否启用SKU管理")
    product_type: str = Field("physical", description="商品类型: virtual=虚拟商品, physical=实物商品, bundle=套餐商品")
    shipping_method: str = Field("express", description="物流方式: express=快递, self_pickup=自提, no_shipping=无需快递")
    shipping_template_id: Optional[str] = Field(None, description="运费模板ID")

    @field_validator('stock')
    @classmethod
    def validate_stock(cls, v, info):
        """验证库存"""
        if info.data.get('stock_unlimited', False):
            return 0
        return v

    @field_validator('payment_mode')
    @classmethod
    def validate_payment_mode(cls, v):
        """验证支付模式"""
        valid_modes = ['points_only', 'cash_only', 'mixed']
        if v not in valid_modes:
            raise ValueError(f"支付模式必须是以下之一: {', '.join(valid_modes)}")
        return v

    @field_validator('cash_price')
    @classmethod
    def validate_cash_price(cls, v, info):
        """验证现金价格"""
        payment_mode = info.data.get('payment_mode', 'points_only')
        if payment_mode == 'cash_only' and v is None:
            raise ValueError("纯现金模式下必须设置现金价格")
        return v

    @field_validator('mixed_points_cost', 'mixed_cash_price')
    @classmethod
    def validate_mixed_prices(cls, v, info):
        """验证混合支付价格"""
        payment_mode = info.data.get('payment_mode', 'points_only')
        if payment_mode == 'mixed':
            field_name = info.field_name
            if field_name == 'mixed_points_cost' and v is None:
                raise ValueError("混合支付模式下必须设置积分价格")
            if field_name == 'mixed_cash_price' and v is None:
                raise ValueError("混合支付模式下必须设置现金价格")
        return v

    @field_validator('product_type')
    @classmethod
    def validate_product_type(cls, v):
        """验证商品类型"""
        valid_types = ['virtual', 'physical', 'bundle']
        if v not in valid_types:
            raise ValueError(f"商品类型必须是以下之一: {', '.join(valid_types)}")
        return v

    @field_validator('shipping_method')
    @classmethod
    def validate_shipping_method(cls, v):
        """验证物流方式"""
        valid_methods = ['express', 'self_pickup', 'no_shipping']
        if v not in valid_methods:
            raise ValueError(f"物流方式必须是以下之一: {', '.join(valid_methods)}")
        return v


class PointProductCreate(PointProductBase):
    """创建商品Schema"""
    image_urls: Optional[List[str]] = Field(None, max_length=6, description="商品图片URLs")

    @field_validator('image_urls')
    @classmethod
    def validate_image_urls(cls, v):
        """验证图片URLs"""
        if v and len(v) > 6:
            raise ValueError("最多支持6张图片")
        return v


class SpecificationInput(BaseModel):
    """规格输入"""
    name: str = Field(..., min_length=1, max_length=50, description="规格名称")
    values: List[str] = Field(default_factory=list, description="规格值列表")


class SKUInput(BaseModel):
    """SKU输入"""
    id: Optional[str] = Field(None, description="SKU ID（更新时需要）")
    sku_code: Optional[str] = Field(None, max_length=50, description="SKU编码")
    specs: dict = Field(default_factory=dict, description="规格组合")
    stock: int = Field(0, ge=0, description="库存")
    stock_unlimited: bool = Field(False, description="无限库存")
    points_cost: int = Field(0, gt=0, description="积分价格")
    image_url: Optional[str] = Field(None, max_length=500, description="SKU图片")
    sort_order: int = Field(0, ge=0, description="排序")
    is_active: bool = Field(True, description="是否启用")


class PointProductUpdate(BaseModel):
    """更新商品Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    points_cost: Optional[int] = Field(None, gt=0)

    # 支付模式（新增）
    payment_mode: Optional[str] = Field(None, description="支付模式")
    cash_price: Optional[int] = Field(None, ge=0, description="现金价格（分）")
    mixed_points_cost: Optional[int] = Field(None, ge=0, description="混合支付时的积分价格")
    mixed_cash_price: Optional[int] = Field(None, ge=0, description="混合支付时的现金价格（分）")

    stock: Optional[int] = Field(None, ge=0)
    stock_unlimited: Optional[bool] = None
    category: Optional[str] = None
    category_id: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    image_urls: Optional[List[str]] = Field(None, max_length=6)
    has_sku: Optional[bool] = None
    product_type: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_template_id: Optional[str] = None
    # SKU相关字段
    specifications: Optional[List[SpecificationInput]] = None
    skus: Optional[List[SKUInput]] = None

    @field_validator('payment_mode')
    @classmethod
    def validate_payment_mode(cls, v):
        """验证支付模式"""
        if v is not None:
            valid_modes = ['points_only', 'cash_only', 'mixed']
            if v not in valid_modes:
                raise ValueError(f"支付模式必须是以下之一: {', '.join(valid_modes)}")
        return v

    @field_validator('image_urls')
    @classmethod
    def validate_image_urls(cls, v):
        """验证图片URLs"""
        if v and len(v) > 6:
            raise ValueError("最多支持6张图片")
        return v

    @field_validator('product_type')
    @classmethod
    def validate_product_type(cls, v):
        """验证商品类型"""
        if v is not None:
            valid_types = ['virtual', 'physical', 'bundle']
            if v not in valid_types:
                raise ValueError(f"商品类型必须是以下之一: {', '.join(valid_types)}")
        return v

    @field_validator('shipping_method')
    @classmethod
    def validate_shipping_method(cls, v):
        """验证物流方式"""
        if v is not None:
            valid_methods = ['express', 'self_pickup', 'no_shipping']
            if v not in valid_methods:
                raise ValueError(f"物流方式必须是以下之一: {', '.join(valid_methods)}")
        return v


class PointProductResponse(PointProductBase):
    """商品响应Schema"""
    id: str
    image_urls: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator('image_urls', mode='before')
    @classmethod
    def parse_image_urls(cls, v):
        """解析图片URLs JSON字符串"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    class Config:
        from_attributes = True


class PointProductListResponse(BaseModel):
    """商品列表响应Schema"""
    id: str
    name: str
    description: Optional[str]
    image_urls: Optional[List[str]]
    image_url: Optional[str]  # 兼容旧版
    points_cost: int

    # 支付模式（新增）
    payment_mode: str = "points_only"
    cash_price: Optional[int] = None
    mixed_points_cost: Optional[int] = None
    mixed_cash_price: Optional[int] = None

    stock: int
    stock_unlimited: bool
    category: Optional[str]
    is_active: bool
    sort_order: int
    product_type: str
    shipping_method: str
    shipping_template_id: Optional[str]
    created_at: datetime

    @field_validator('image_urls', mode='before')
    @classmethod
    def parse_image_urls(cls, v):
        """解析图片URLs JSON字符串"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    @field_validator('image_url', mode='before')
    @classmethod
    def parse_image_url(cls, v, info):
        """解析主图片URL"""
        if v:
            return v
        image_urls = info.data.get('image_urls', [])
        return image_urls[0] if image_urls else None

    class Config:
        from_attributes = True