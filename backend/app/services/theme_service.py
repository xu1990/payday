"""
主题与设置服务 - Sprint 3.4；主题管理、用户隐私/消息设置
"""
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.theme import Theme, UserSetting
from app.models.user import User


async def list_themes(db: AsyncSession) -> List[Theme]:
    """获取所有可用主题（系统主题 + 用户主题）"""
    system_themes = await db.execute(
        select(Theme).where(Theme.is_system == 1).order_by(Theme.created_at)
    )
    return list(system_themes.scalars().all())


async def get_user_settings(db: AsyncSession, user_id: str) -> dict:
    """获取用户设置（主题ID、隐私、消息开关）"""
    result = await db.execute(
        select(UserSetting).where(UserSetting.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        return {
            "theme_id": None,
            "privacy_profile": 0,
            "allow_stranger_notice": 1,
            "allow_comment": 1,
        }

    return {
        "theme_id": settings.theme_id,
        "privacy_profile": settings.privacy_profile if settings.privacy_profile is not None else 0,
        "allow_stranger_notice": settings.allow_stranger_notice if settings.allow_stranger_notice is not None else 1,
        "allow_comment": settings.allow_comment if settings.allow_comment is not None else 1,
    }


async def update_user_settings(
    db: AsyncSession,
    user_id: str,
    theme_id: Optional[str] = None,
    privacy_profile: Optional[int] = None,
    allow_stranger_notice: Optional[int] = None,
    allow_comment: Optional[int] = None,
) -> Optional[UserSetting]:
    """更新用户设置"""
    settings = await db.execute(
        select(UserSetting).where(UserSetting.user_id == user_id)
    )
    obj = settings.scalar_one_or_none()
    if not obj:
        # 创建新设置
        obj = UserSetting(
            user_id=user_id,
            theme_id=theme_id or await _get_default_theme_id(db),
            privacy_profile=privacy_profile if privacy_profile is not None else 0,
            allow_stranger_notice=allow_stranger_notice if allow_stranger_notice is not None else 1,
            allow_comment=allow_comment if allow_comment is not None else 1,
        )
        db.add(obj)
    else:
        # 更新现有设置
        if theme_id is not None:
            obj.theme_id = theme_id
        if privacy_profile is not None:
            obj.privacy_profile = privacy_profile
        if allow_stranger_notice is not None:
            obj.allow_stranger_notice = allow_stranger_notice
        if allow_comment is not None:
            obj.allow_comment = allow_comment

    await db.commit()
    await db.refresh(obj)
    return obj


async def _get_default_theme_id(db: AsyncSession) -> str:
    """获取默认主题ID"""
    theme = await db.execute(
        select(Theme).where(Theme.is_system == 1, Theme.name == "默认").order_by(Theme.created_at)
    )
    default = theme.scalar_one_or_none()
    return default.id if default else ""
