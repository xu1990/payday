"""
缓存管理 API - 用于缓存预热和管理
"""
from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.cache import PreheatResponse
from app.core.deps import get_db, get_current_admin_user
from app.services.cache_preheat import preheat_all
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


@router.post("/preheat", response_model=PreheatResponse)
async def trigger_cache_preheat(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """
    触发缓存预热

    预热以下数据:
    - 热门帖子
    - 活跃话题
    - 会员套餐
    - 主题配置
    - 统计数据

    需要管理员权限
    """
    try:
        results = await preheat_all(db)
        return PreheatResponse(
            success=True,
            message=f"缓存预热完成，共预热 {sum(results.values())} 项",
            details=results,
        )
    except Exception as e:
        logger.error(f"Cache preheating failed: {e}")
        return PreheatResponse(
            success=False,
            message=f"缓存预热失败: {str(e)}",
            details={},
        )


@router.get("/stats")
async def get_cache_stats(_admin=Depends(get_current_admin_user)):
    """
    获取缓存统计信息

    需要管理员权限
    """
    import redis
    from app.core.config import get_settings

    settings = get_settings()
    r = redis.from_url(settings.redis_url)

    info = r.info()
    keyspace = info.get("keyspace", {})
    stats = {
        "connected_clients": info.get("connected_clients", 0),
        "used_memory_human": info.get("used_memory_human", "0B"),
        "keyspace": keyspace,
        "total_keys": sum(db.get("keys", 0) for db in keyspace.values()),
    }

    return stats
