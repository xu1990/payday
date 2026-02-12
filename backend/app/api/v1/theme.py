"""
主题与设置接口 - Sprint 3.4；主题列表、用户设置管理
"""
from typing import Optional

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.theme import Theme, UserSetting
from app.schemas.theme import ThemeListResponse, UserSettingsResponse, UserSettingsUpdate
from app.services.theme_service import list_themes, get_user_settings, update_user_settings
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("", response_model=ThemeListResponse)
async def list_themes_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有可用主题（系统主题）"""
    themes = await list_themes(db)
    return ThemeListResponse(items=themes)


@router.get("/my-settings", response_model=UserSettingsResponse)
async def get_my_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的设置"""
    settings = await get_user_settings(db, current_user.id)
    return UserSettingsResponse(**settings)


@router.put("/my-settings", response_model=UserSettingsResponse)
async def update_my_settings(
    body: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户设置"""
    settings = await update_user_settings(
        db,
        current_user.id,
        theme_id=body.theme_id,
        privacy_profile=body.privacy_profile,
        allow_stranger_notice=body.allow_stranger_notice,
        allow_comment=body.allow_comment,
    )
    return UserSettingsResponse(**settings)
