"""
运费模板管理接口 - 管理后台
Shipping Template Management API - Admin Panel

提供运费模板和区域的管理功能：
- POST /admin/shipping-templates - 创建运费模板
- GET /admin/shipping-templates - 获取运费模板列表
- GET /admin/shipping-templates/{id} - 获取单个运费模板
- PUT /admin/shipping-templates/{id} - 更新运费模板
- DELETE /admin/shipping-templates/{id} - 删除运费模板
- GET /admin/shipping-templates/{id}/regions - 获取模板区域列表
- POST /admin/shipping-templates/{id}/regions - 添加模板区域
- PUT /admin/shipping-template-regions/{region_id} - 更新模板区域
- DELETE /admin/shipping-template-regions/{region_id} - 删除模板区域

关键特性：
- 使用ShippingTemplateService处理业务逻辑
- JWT认证保护所有端点（需要admin scope）
- 完整的CRUD操作
- 区域配置管理
- 软删除机制
- 统一错误处理
"""
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import (BusinessException, NotFoundException, ValidationException,
                                 success_response)
from app.models.user import User
from app.schemas.shipping import (ShippingTemplateCreate, ShippingTemplateRegionCreate,
                                  ShippingTemplateRegionResponse, ShippingTemplateRegionUpdate,
                                  ShippingTemplateResponse, ShippingTemplateUpdate)
from app.services.shipping_service import ShippingTemplateService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin/shipping-templates", tags=["admin-shipping"])


# ==================== 运费模板管理 ====================

@router.get("", response_model=dict, summary="获取运费模板列表")
async def list_shipping_templates(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取运费模板列表"""
    service = ShippingTemplateService(db)

    templates = await service.list_templates(
        skip=offset,  # 服务使用 skip 而不是 offset
        limit=limit
    )

    # 如果 active_only 为 True，过滤结果
    if active_only:
        templates = [t for t in templates if t.is_active]

    # 转换为响应格式
    items = []
    for template in templates:
        item = ShippingTemplateResponse.model_validate(template).model_dump(mode='json')
        items.append(item)

    return success_response(
        data={"items": items, "total": len(items)},
        message="获取运费模板列表成功"
    )


@router.post("", response_model=dict, summary="创建运费模板")
async def create_shipping_template(
    data: ShippingTemplateCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建运费模板"""
    service = ShippingTemplateService(db)

    template = await service.create_template(data)

    result = ShippingTemplateResponse.model_validate(template).model_dump(mode='json')

    return success_response(data=result, message="创建运费模板成功")


@router.get("/{template_id}", response_model=dict, summary="获取单个运费模板")
async def get_shipping_template(
    template_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个运费模板"""
    service = ShippingTemplateService(db)

    template = await service.get_template(template_id)

    result = ShippingTemplateResponse.model_validate(template).model_dump(mode='json')

    return success_response(data=result, message="获取运费模板成功")


@router.put("/{template_id}", response_model=dict, summary="更新运费模板")
async def update_shipping_template(
    template_id: str,
    data: ShippingTemplateUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新运费模板"""
    service = ShippingTemplateService(db)

    template = await service.update_template(template_id, data)

    result = ShippingTemplateResponse.model_validate(template).model_dump(mode='json')

    return success_response(data=result, message="更新运费模板成功")


@router.delete("/{template_id}", response_model=dict, summary="删除运费模板")
async def delete_shipping_template(
    template_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除运费模板"""
    service = ShippingTemplateService(db)

    await service.delete_template(template_id)

    return success_response(data={"deleted": True}, message="删除运费模板成功")


# ==================== 运费模板区域管理 ====================

@router.get("/{template_id}/regions", response_model=dict, summary="获取模板区域列表")
async def list_template_regions(
    template_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定模板的区域配置列表"""
    service = ShippingTemplateService(db)

    regions = await service.list_regions(template_id)

    # 转换为响应格式
    items = []
    for region in regions:
        item = ShippingTemplateRegionResponse.model_validate(region).model_dump(mode='json')
        items.append(item)

    return success_response(
        data={"items": items, "total": len(items)},
        message="获取区域配置列表成功"
    )


@router.post("/{template_id}/regions", response_model=dict, summary="添加模板区域")
async def create_template_region(
    template_id: str,
    data: ShippingTemplateRegionCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """为指定模板添加区域配置"""
    service = ShippingTemplateService(db)

    region = await service.create_region(template_id, data)

    result = ShippingTemplateRegionResponse.model_validate(region).model_dump(mode='json')

    return success_response(data=result, message="添加区域配置成功")


@router.put("/shipping-template-regions/{region_id}", response_model=dict, summary="更新模板区域")
async def update_template_region(
    region_id: str,
    data: ShippingTemplateRegionUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新模板区域配置"""
    service = ShippingTemplateService(db)

    region = await service.update_region(region_id, data)

    result = ShippingTemplateRegionResponse.model_validate(region).model_dump(mode='json')

    return success_response(data=result, message="更新区域配置成功")


@router.delete("/shipping-template-regions/{region_id}", response_model=dict, summary="删除模板区域")
async def delete_template_region(
    region_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除模板区域配置"""
    service = ShippingTemplateService(db)

    await service.delete_region(region_id)

    return success_response(data={"deleted": True}, message="删除区域配置成功")