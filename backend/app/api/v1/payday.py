"""
发薪日配置 - 当前用户的 list/create/get/update/delete
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.core.exceptions import NotFoundException, AuthenticationException, BusinessException, success_response
from app.core.database import get_db
from app.models.user import User
from app.schemas.payday import PaydayConfigCreate, PaydayConfigResponse, PaydayConfigUpdate
from app.services.payday_service import (
    create as create_config,
    delete as delete_config,
    get_by_id,
    list_by_user,
    update as update_config,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/payday", tags=["payday"])


@router.get("")
async def payday_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    configs = await list_by_user(db, current_user.id)
    data = [PaydayConfigResponse.model_validate(c).model_dump(mode='json') for c in configs]
    return success_response(data=data, message="获取发薪日配置成功")


@router.post("")
async def payday_create(
    body: PaydayConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await create_config(db, current_user.id, body)
    return success_response(data=PaydayConfigResponse.model_validate(config).model_dump(mode='json'), message="创建发薪日配置成功")


@router.get("/{config_id}")
async def payday_get(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await get_by_id(db, config_id, current_user.id)
    if not config:
        raise NotFoundException("资源不存在")
    return success_response(data=PaydayConfigResponse.model_validate(config).model_dump(mode='json'), message="获取发薪日配置成功")


@router.put("/{config_id}")
async def payday_update(
    config_id: str,
    body: PaydayConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await update_config(db, config_id, current_user.id, body)
    if not config:
        raise NotFoundException("资源不存在")
    return success_response(data=PaydayConfigResponse.model_validate(config).model_dump(mode='json'), message="更新发薪日配置成功")


@router.delete("/{config_id}")
async def payday_delete(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_config(db, config_id, current_user.id)
    if not ok:
        raise NotFoundException("资源不存在")
    return success_response(message="删除发薪日配置成功")
