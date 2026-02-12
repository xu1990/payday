"""
存储服务状态检查 API - 查看 COS/OSS 配置状态
"""
from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin_user
from app.models.user import User
from app.utils.storage import storage_service

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/status")
async def get_storage_status():
    """
    获取存储服务状态（公开接口）

    Returns:
        存储服务配置和健康状态
    """
    return storage_service.get_status()


@router.get("/config")
async def get_storage_config(current_admin: User = Depends(get_current_admin_user)):
    """
    获取存储服务详细配置（管理员接口）

    Returns:
        存储服务详细配置信息
    """
    from app.core.config import settings

    return {
        "provider": settings.storage_provider,
        "cos": {
            "enabled": storage_service.cos_enabled,
            "bucket": settings.cos_bucket if storage_service.cos_enabled else None,
            "region": settings.cos_region if storage_service.cos_enabled else None,
        },
        "oss": {
            "enabled": storage_service.oss_enabled,
            "bucket": settings.oss_bucket if storage_service.oss_enabled else None,
            "endpoint": settings.oss_endpoint if storage_service.oss_enabled else None,
        },
    }
