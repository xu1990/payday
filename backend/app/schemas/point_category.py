"""积分商品分类Schema - Sprint 4.7 商品兑换系统"""
from datetime import datetime
from typing import List, Optional

from app.models.point_category import PointCategory
from pydantic import BaseModel, Field, validator


class PointCategoryBase(BaseModel):
    """分类基础Schema"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[str] = Field(None, description="父分类ID")
    icon_url: Optional[str] = Field(None, max_length=500, description="分类图标URL")
    banner_url: Optional[str] = Field(None, max_length=500, description="分类横幅URL")
    level: int = Field(..., ge=1, le=3, description="层级(1/2/3)")
    sort_order: int = Field(0, ge=0, description="排序权重")
    is_active: bool = Field(True, description="是否启用")

    @validator('level')
    def validate_level(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError("层级必须是1、2或3")
        return v

    @validator('parent_id')
    def validate_parent_level(cls, v, values):
        """验证父分类层级"""
        level = values.get('level')
        if v and level == 1:
            raise ValueError("一级分类不能有父分类")
        return v


class PointCategoryCreate(PointCategoryBase):
    """创建分类Schema"""
    pass


class PointCategoryUpdate(BaseModel):
    """更新分类Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    icon_url: Optional[str] = Field(None, max_length=500)
    banner_url: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class PointCategoryResponse(PointCategoryBase):
    """分类响应Schema"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PointCategoryTree(PointCategoryResponse):
    """分类树Schema"""
    children: Optional[List['PointCategoryTree']] = []

    class Config:
        from_attributes = True


# Forward reference for recursive type
PointCategoryTree.model_rebuild()