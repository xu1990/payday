"""
规格模板管理接口 - 管理后台
"""
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import success_response
from app.models.user import User
from app.services.specification_template_service import (
    create_template,
    delete_template,
    get_template,
    list_templates,
    template_to_dict,
    update_template,
)
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin/specification-templates", tags=["admin-specification-templates"])


# ==================== Request/Response Schemas ====================

class TemplateCreate(BaseModel):
    """创建模板请求"""
    name: str = Field(..., max_length=50, description="规格名称")
    description: Optional[str] = Field(None, max_length=200, description="规格描述")
    values: List[str] = Field(..., min_length=1, description="规格值列表")
    sort_order: int = Field(0, description="排序权重")
    is_active: bool = Field(True, description="是否启用")


class TemplateUpdate(BaseModel):
    """更新模板请求"""
    name: Optional[str] = Field(None, max_length=50, description="规格名称")
    description: Optional[str] = Field(None, max_length=200, description="规格描述")
    values: Optional[List[str]] = Field(None, min_length=1, description="规格值列表")
    sort_order: Optional[int] = Field(None, description="排序权重")
    is_active: Optional[bool] = Field(None, description="是否启用")


# ==================== API Endpoints ====================

@router.get("")
async def list_specification_templates(
    active_only: bool = Query(False, description="是否只返回启用的模板"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取规格模板列表"""
    templates = await list_templates(db, active_only=active_only)

    data = [template_to_dict(t) for t in templates]

    return success_response(
        data={"templates": data, "total": len(data)},
        message="获取规格模板列表成功"
    )


@router.post("")
async def create_specification_template(
    body: TemplateCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建规格模板"""
    template = await create_template(
        db,
        name=body.name,
        values=body.values,
        description=body.description,
        sort_order=body.sort_order,
        is_active=body.is_active,
    )

    return success_response(
        data={"id": template.id},
        message="创建规格模板成功"
    )


@router.get("/{template_id}")
async def get_specification_template(
    template_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个规格模板详情"""
    template = await get_template(db, template_id)

    return success_response(
        data=template_to_dict(template),
        message="获取规格模板成功"
    )


@router.put("/{template_id}")
async def update_specification_template(
    template_id: str,
    body: TemplateUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新规格模板"""
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}

    template = await update_template(db, template_id, **update_data)

    return success_response(
        data=template_to_dict(template),
        message="更新规格模板成功"
    )


@router.delete("/{template_id}")
async def delete_specification_template(
    template_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除规格模板"""
    await delete_template(db, template_id)

    return success_response(
        data={"deleted": True},
        message="删除规格模板成功"
    )
