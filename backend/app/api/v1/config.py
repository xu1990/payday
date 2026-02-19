"""
公共配置 API - 小程序获取协议、开屏配置等
"""
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import success_response
from app.models.miniprogram_config import MiniprogramConfig
from typing import Optional

router = APIRouter(prefix="/config", tags=["public-config"])


class AgreementResponse(BaseModel):
    user_agreement: Optional[str] = None
    privacy_agreement: Optional[str] = None


class SplashConfigResponse(BaseModel):
    image_url: Optional[str] = None
    content: Optional[str] = None
    countdown: int = 3
    is_active: bool = False


@router.get("/public/agreements")
async def get_public_agreements(
    db: AsyncSession = Depends(get_db),
):
    """获取用户协议和隐私协议（公开接口）"""
    from sqlalchemy import select

    # 获取用户协议
    user_result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'user_agreement')
    )
    user_config = user_result.scalar_one_or_none()
    user_agreement = user_config.value if user_config else None

    # 获取隐私协议
    privacy_result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'privacy_agreement')
    )
    privacy_config = privacy_result.scalar_one_or_none()
    privacy_agreement = privacy_config.value if privacy_config else None

    return success_response(
        data=AgreementResponse(
            user_agreement=user_agreement,
            privacy_agreement=privacy_agreement
        ).model_dump(),
        message="获取协议成功"
    )


@router.get("/public/splash")
async def get_public_splash_config(
    db: AsyncSession = Depends(get_db),
):
    """获取开屏页面配置（公开接口）"""
    from sqlalchemy import select
    import json

    result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'splash_config')
    )
    config = result.scalar_one_or_none()

    if not config or not config.value or not config.is_active:
        return success_response(
            data=SplashConfigResponse(is_active=False).model_dump(),
            message="开屏配置未启用"
        )

    try:
        splash_data = json.loads(config.value)
        return success_response(
            data=SplashConfigResponse(
                image_url=splash_data.get('image_url'),
                content=splash_data.get('content'),
                countdown=splash_data.get('countdown', 3),
                is_active=True
            ).model_dump(),
            message="获取开屏配置成功"
        )
    except (json.JSONDecodeError, TypeError):
        return success_response(
            data=SplashConfigResponse(is_active=False).model_dump(),
            message="开屏配置格式错误"
        )
