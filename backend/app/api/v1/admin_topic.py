"""
话题管理接口 - 管理后台
"""
from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicUpdate, TopicResponse, TopicListResponse
from app.services import topic_service

router = APIRouter(prefix="/admin/topics", tags=["admin-topics"])


@router.get("", response_model=TopicListResponse)
async def list_topics(
    active_only: bool = Query(False, description="仅启用的"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取话题列表（分页）。"""
    items, total = await topic_service.list_topics(
        db, active_only=active_only, limit=limit, offset=offset
    )
    return TopicListResponse(
        items=[TopicResponse.model_validate(t) for t in items], total=total
    )


@router.post("", response_model=TopicResponse)
async def create_topic(
    data: TopicCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建话题。"""
    topic = await topic_service.create_topic(
        db,
        name=data.name,
        description=data.description,
        cover_image=data.cover_image,
        sort_order=data.sort_order,
    )
    return TopicResponse.model_validate(topic)


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个话题。"""
    topic = await topic_service.get_topic_by_id(db, topic_id)
    if not topic:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="话题不存在")
    return TopicResponse.model_validate(topic)


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: str,
    data: TopicUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新话题。"""
    topic = await topic_service.update_topic(
        db,
        topic_id=topic_id,
        name=data.name,
        description=data.description,
        cover_image=data.cover_image,
        is_active=data.is_active,
        sort_order=data.sort_order,
    )
    if not topic:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="话题不存在")
    return TopicResponse.model_validate(topic)


@router.delete("/{topic_id}")
async def delete_topic(
    topic_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除话题。"""
    success = await topic_service.delete_topic(db, topic_id)
    if not success:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="话题不存在")
    return {"deleted": success}
