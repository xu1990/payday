"""Point SKU Schemas - 积分商品SKU数据验证（Sprint 4.7）"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ============== Specification Schemas ==============
class SpecificationCreate(BaseModel):
    """创建规格请求"""
    name: str = Field(..., min_length=1, max_length=50, description="规格名称（如：颜色、尺寸）")
    sort_order: int = Field(0, description="排序权重")


class SpecificationUpdate(BaseModel):
    """更新规格请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="规格名称")
    sort_order: Optional[int] = Field(None, description="排序权重")


class SpecificationResponse(BaseModel):
    """规格响应"""
    id: str
    product_id: str
    name: str
    sort_order: int
    created_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_db(cls, spec) -> "SpecificationResponse":
        """从数据库模型创建响应"""
        return cls(
            id=spec.id,
            product_id=spec.product_id,
            name=spec.name,
            sort_order=spec.sort_order,
            created_at=spec.created_at.isoformat()
        )


# ============== Specification Value Schemas ==============
class SpecificationValueCreate(BaseModel):
    """创建规格值请求"""
    value: str = Field(..., min_length=1, max_length=50, description="规格值（如：红色、L）")
    sort_order: int = Field(0, description="排序权重")


class SpecificationValueUpdate(BaseModel):
    """更新规格值请求"""
    value: Optional[str] = Field(None, min_length=1, max_length=50, description="规格值")
    sort_order: Optional[int] = Field(None, description="排序权重")


class SpecificationValueResponse(BaseModel):
    """规格值响应"""
    id: str
    specification_id: str
    value: str
    sort_order: int
    created_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_db(cls, spec_value) -> "SpecificationValueResponse":
        """从数据库模型创建响应"""
        return cls(
            id=spec_value.id,
            specification_id=spec_value.specification_id,
            value=spec_value.value,
            sort_order=spec_value.sort_order,
            created_at=spec_value.created_at.isoformat()
        )


# ============== SKU Schemas ==============
class SKUCreate(BaseModel):
    """创建SKU请求"""
    sku_code: str = Field(..., min_length=1, max_length=50, description="SKU编码（唯一）")
    specs: Dict[str, str] = Field(..., description="规格组合（如：{\"颜色\": \"红色\", \"尺寸\": \"L\"}）")
    stock: int = Field(..., ge=0, description="库存数量")
    points_cost: int = Field(..., gt=0, description="积分价格")
    stock_unlimited: bool = Field(False, description="库存无限")
    image_url: Optional[str] = Field(None, max_length=500, description="SKU专属图片（兼容旧版）")
    image_urls: Optional[List[str]] = Field(None, max_length=6, description="SKU图片URLs列表")
    sort_order: int = Field(0, description="排序权重")


class SKUUpdate(BaseModel):
    """更新SKU请求"""
    sku_code: Optional[str] = Field(None, min_length=1, max_length=50, description="SKU编码")
    specs: Optional[Dict[str, str]] = Field(None, description="规格组合")
    stock: Optional[int] = Field(None, ge=0, description="库存数量")
    points_cost: Optional[int] = Field(None, gt=0, description="积分价格")
    stock_unlimited: Optional[bool] = Field(None, description="库存无限")
    image_url: Optional[str] = Field(None, max_length=500, description="SKU专属图片（兼容旧版）")
    image_urls: Optional[List[str]] = Field(None, max_length=6, description="SKU图片URLs列表")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序权重")


class SKUResponse(BaseModel):
    """SKU响应"""
    id: str
    product_id: str
    sku_code: str
    specs: Dict[str, str]
    stock: int
    stock_unlimited: bool
    points_cost: int
    image_url: Optional[str]  # 兼容旧版
    image_urls: Optional[List[str]]  # 多图支持
    is_active: bool
    sort_order: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_db(cls, sku) -> "SKUResponse":
        """从数据库模型创建响应"""
        import json

        # 解析specs JSON
        try:
            specs_dict = json.loads(sku.specs) if isinstance(sku.specs, str) else sku.specs
        except:
            specs_dict = {}

        # 解析image_urls JSON
        image_urls = None
        if hasattr(sku, 'image_urls') and sku.image_urls:
            try:
                image_urls = json.loads(sku.image_urls) if isinstance(sku.image_urls, str) else sku.image_urls
            except:
                image_urls = None

        # 兼容旧版：如果没有image_urls但有image_url，转换为列表
        if not image_urls and sku.image_url:
            image_urls = [sku.image_url]

        return cls(
            id=sku.id,
            product_id=sku.product_id,
            sku_code=sku.sku_code,
            specs=specs_dict,
            stock=sku.stock,
            stock_unlimited=sku.stock_unlimited,
            points_cost=sku.points_cost,
            image_url=sku.image_url,  # 保留兼容性
            image_urls=image_urls,
            is_active=sku.is_active,
            sort_order=sku.sort_order,
            created_at=sku.created_at.isoformat(),
            updated_at=sku.updated_at.isoformat()
        )


class SKUBatchUpdateItem(BaseModel):
    """批量更新SKU单项"""
    id: str = Field(..., description="SKU ID")
    stock: Optional[int] = Field(None, ge=0, description="库存数量")
    points_cost: Optional[int] = Field(None, gt=0, description="积分价格")
    is_active: Optional[bool] = Field(None, description="是否启用")
    stock_unlimited: Optional[bool] = Field(None, description="是否不限库存")
    image_url: Optional[str] = Field(None, description="SKU主图")
    sort_order: Optional[int] = Field(None, ge=0, description="排序值，值越大越靠前")


class SKUBatchUpdate(BaseModel):
    """批量更新SKU请求"""
    skus: List[SKUBatchUpdateItem] = Field(..., min_length=1, description="SKU更新列表")
