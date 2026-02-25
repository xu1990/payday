"""
物流和退货 - 请求/响应模型
Shipping and Returns - Request/Response Schemas

包含所有物流和退货相关的Pydantic模型：
- ShipmentCreate - 创建发货记录
- ShipmentResponse - 发货记录响应
- TrackingUpdate - 更新物流状态
- ReturnCreate - 创建退货申请
- ReturnResponse - 退货记录响应
- ReturnApprove - 审批退货
- ReturnReject - 拒绝退货
- RefundProcess - 处理退款
- ShippingTemplateCreate - 创建运费模板
- ShippingTemplateUpdate - 更新运费模板
- ShippingTemplateResponse - 运费模板响应
- ShippingTemplateRegionCreate - 创建运费模板区域
- ShippingTemplateRegionUpdate - 更新运费模板区域
- ShippingTemplateRegionResponse - 运费模板区域响应
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class ShipmentCreate(BaseModel):
    """创建发货记录请求"""
    courier_code: str = Field(..., min_length=1, max_length=20, description="物流公司代码")
    tracking_number: str = Field(..., min_length=1, max_length=50, description="物流单号")


class ShipmentResponse(BaseModel):
    """发货记录响应"""
    id: str
    order_id: str
    courier_code: str
    courier_name: str
    tracking_number: str
    status: str
    shipped_at: datetime
    delivered_at: Optional[datetime] = None
    tracking_info: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True


class TrackingUpdate(BaseModel):
    """更新物流状态请求"""
    status: Literal["pending", "picked_up", "in_transit", "delivered", "failed"] = Field(
        ..., description="物流状态"
    )
    tracking_info: Optional[List[Dict[str, Any]]] = Field(
        None, description="物流跟踪详情"
    )


class ReturnCreate(BaseModel):
    """创建退货申请请求"""
    order_item_id: str = Field(..., description="订单明细ID")
    reason: Literal[
        "quality_issue", "damaged", "wrong_item",
        "not_as_described", "no_longer_needed", "other"
    ] = Field(..., description="退货原因")
    return_type: Literal["refund_only", "replace", "return_and_refund"] = Field(
        ..., description="退货类型"
    )
    description: Optional[str] = Field(None, max_length=500, description="退货说明")
    images: Optional[List[str]] = Field(None, description="凭证图片URL列表")


class ReturnResponse(BaseModel):
    """退货记录响应"""
    id: str
    order_id: str
    order_item_id: str
    return_reason: str
    return_description: Optional[str] = None
    images: Optional[List[str]] = None
    return_type: str
    status: str
    refund_amount: Optional[Decimal] = None
    refund_transaction_id: Optional[str] = None
    requested_at: datetime
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    admin_id: Optional[str] = None
    admin_notes: Optional[str] = None

    class Config:
        from_attributes = True

    @field_serializer('refund_amount')
    def serialize_refund_amount(self, value: Optional[Decimal]) -> Optional[str]:
        """Serialize refund_amount Decimal to string"""
        if value is None:
            return None
        return str(value)


class ReturnApprove(BaseModel):
    """审批退货请求"""
    notes: Optional[str] = Field(None, max_length=500, description="管理员备注")


class ReturnReject(BaseModel):
    """拒绝退货请求"""
    notes: Optional[str] = Field(None, max_length=500, description="拒绝原因")


class RefundProcess(BaseModel):
    """处理退款请求"""
    refund_amount: Decimal = Field(..., gt=0, description="退款金额")
    transaction_id: Optional[str] = Field(None, max_length=100, description="退款交易ID")

    @field_validator("refund_amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """验证退款金额"""
        if v <= 0:
            raise ValueError("退款金额必须大于0")
        return v


# ==================== Courier Schemas ====================

class CourierCreate(BaseModel):
    """创建物流公司请求"""
    name: str = Field(..., min_length=1, max_length=100, description="物流公司名称")
    code: str = Field(..., min_length=1, max_length=50, description="物流公司代码")
    website: Optional[str] = Field(None, max_length=200, description="官网地址")
    tracking_url: Optional[str] = Field(None, max_length=200, description="物流查询URL")
    supports_cod: bool = Field(False, description="是否支持货到付款")
    supports_cold_chain: bool = Field(False, description="是否支持冷链")
    sort_order: int = Field(0, description="排序顺序")
    is_active: bool = Field(True, description="是否启用")


class CourierUpdate(BaseModel):
    """更新物流公司请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="物流公司名称")
    website: Optional[str] = Field(None, max_length=200, description="官网地址")
    tracking_url: Optional[str] = Field(None, max_length=200, description="物流查询URL")
    supports_cod: Optional[bool] = Field(None, description="是否支持货到付款")
    supports_cold_chain: Optional[bool] = Field(None, description="是否支持冷链")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否启用")


class CourierResponse(BaseModel):
    """物流公司响应"""
    id: str
    name: str
    code: str
    website: Optional[str] = None
    tracking_url: Optional[str] = None
    supports_cod: bool
    supports_cold_chain: bool
    sort_order: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Shipping Template Schemas ====================

class ShippingTemplateCreate(BaseModel):
    """创建运费模板请求"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=200, description="模板描述")
    charge_type: Literal["weight", "quantity", "fixed"] = Field(..., description="计费方式")
    default_first_unit: int = Field(..., gt=0, description="首件/首重")
    default_first_cost: int = Field(..., ge=0, description="首件运费(分)")
    default_continue_unit: int = Field(..., gt=0, description="续件/续重")
    default_continue_cost: int = Field(..., ge=0, description="续件运费(分)")
    free_threshold: Optional[int] = Field(None, ge=0, description="包邮门槛(分)")
    estimate_days_min: Optional[int] = Field(None, gt=0, description="预计到达最少天数")
    estimate_days_max: Optional[int] = Field(None, gt=0, description="预计到达最多天数")

    @field_validator("estimate_days_max")
    @classmethod
    def validate_estimate_days(cls, v, info):
        """验证最大天数不能小于最小天数"""
        if v is not None and info.data.get("estimate_days_min") is not None:
            if v < info.data["estimate_days_min"]:
                raise ValueError("最大天数不能小于最小天数")
        return v


class ShippingTemplateUpdate(BaseModel):
    """更新运费模板请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=200, description="模板描述")
    charge_type: Optional[Literal["weight", "quantity", "fixed"]] = Field(None, description="计费方式")
    default_first_unit: Optional[int] = Field(None, gt=0, description="首件/首重")
    default_first_cost: Optional[int] = Field(None, ge=0, description="首件运费(分)")
    default_continue_unit: Optional[int] = Field(None, gt=0, description="续件/续重")
    default_continue_cost: Optional[int] = Field(None, ge=0, description="续件运费(分)")
    free_threshold: Optional[int] = Field(None, ge=0, description="包邮门槛(分)")
    estimate_days_min: Optional[int] = Field(None, gt=0, description="预计到达最少天数")
    estimate_days_max: Optional[int] = Field(None, gt=0, description="预计到达最多天数")
    is_active: Optional[bool] = Field(None, description="是否启用")

    @field_validator("estimate_days_max")
    @classmethod
    def validate_estimate_days(cls, v, info):
        """验证最大天数不能小于最小天数"""
        if v is not None and info.data.get("estimate_days_min") is not None:
            if v < info.data["estimate_days_min"]:
                raise ValueError("最大天数不能小于最小天数")
        return v


class ShippingTemplateResponse(BaseModel):
    """运费模板响应"""
    id: str
    name: str
    description: Optional[str] = None
    charge_type: str
    default_first_unit: int
    default_first_cost: int
    default_continue_unit: int
    default_continue_cost: int
    free_threshold: Optional[int] = None
    estimate_days_min: Optional[int] = None
    estimate_days_max: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShippingTemplateRegionCreate(BaseModel):
    """创建运费模板区域请求"""
    region_codes: str = Field(..., min_length=1, description="区域代码列表(逗号分隔)")
    region_names: str = Field(..., min_length=1, description="区域名称列表(逗号分隔)")
    first_unit: int = Field(..., gt=0, description="首件/首重")
    first_cost: int = Field(..., ge=0, description="首件运费(分)")
    continue_unit: int = Field(..., gt=0, description="续件/续重")
    continue_cost: int = Field(..., ge=0, description="续件运费(分)")
    free_threshold: Optional[int] = Field(None, ge=0, description="包邮门槛(分)")

    @field_validator("region_codes", "region_names")
    @classmethod
    def validate_region_format(cls, v):
        """验证区域格式"""
        if not v.strip():
            raise ValueError("区域代码和名称不能为空")
        return v.strip()


class ShippingTemplateRegionUpdate(BaseModel):
    """更新运费模板区域请求"""
    region_codes: Optional[str] = Field(None, min_length=1, description="区域代码列表(逗号分隔)")
    region_names: Optional[str] = Field(None, min_length=1, description="区域名称列表(逗号分隔)")
    first_unit: Optional[int] = Field(None, gt=0, description="首件/首重")
    first_cost: Optional[int] = Field(None, ge=0, description="首件运费(分)")
    continue_unit: Optional[int] = Field(None, gt=0, description="续件/续重")
    continue_cost: Optional[int] = Field(None, ge=0, description="续件运费(分)")
    free_threshold: Optional[int] = Field(None, ge=0, description="包邮门槛(分)")
    is_active: Optional[bool] = Field(None, description="是否启用")

    @field_validator("region_codes", "region_names")
    @classmethod
    def validate_region_format(cls, v):
        """验证区域格式"""
        if v is not None and not v.strip():
            raise ValueError("区域代码和名称不能为空")
        return v.strip() if v is not None else v


class ShippingTemplateRegionResponse(BaseModel):
    """运费模板区域响应"""
    id: str
    template_id: str
    region_codes: str
    region_names: str
    first_unit: int
    first_cost: int
    continue_unit: int
    continue_cost: int
    free_threshold: Optional[int] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
