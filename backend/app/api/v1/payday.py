"""
发薪日配置 - 当前用户的 list/create/get/update/delete
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
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


@router.get("", response_model=list[PaydayConfigResponse])
async def payday_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    configs = await list_by_user(db, current_user.id)
    return [PaydayConfigResponse.model_validate(c) for c in configs]


@router.post("", response_model=PaydayConfigResponse)
async def payday_create(
    body: PaydayConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await create_config(db, current_user.id, body)
    return PaydayConfigResponse.model_validate(config)


@router.get("/{config_id}", response_model=PaydayConfigResponse)
async def payday_get(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await get_by_id(db, config_id, current_user.id)
    if not config:
        raise HTTPException(status_code=404, detail="发薪日配置不存在")
    return PaydayConfigResponse.model_validate(config)


@router.put("/{config_id}", response_model=PaydayConfigResponse)
async def payday_update(
    config_id: str,
    body: PaydayConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await update_config(db, config_id, current_user.id, body)
    if not config:
        raise HTTPException(status_code=404, detail="发薪日配置不存在")
    return PaydayConfigResponse.model_validate(config)


@router.delete("/{config_id}", status_code=204)
async def payday_delete(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_config(db, config_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="发薪日配置不存在")
