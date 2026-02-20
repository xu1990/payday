"""
话题公开接口 - 小程序端
"""
from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import success_response
from app.schemas.topic import TopicResponse
from app.services import topic_service

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/active")
async def get_active_topics(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """获取启用的话题列表（公开接口，无需认证）。"""
    items, total = await topic_service.list_topics(
        db, active_only=True, limit=limit, offset=offset
    )
    return success_response(
        data=[TopicResponse.model_validate(t).model_dump(mode='json') for t in items],
        message="获取话题列表成功"
    )
