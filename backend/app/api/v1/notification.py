"""
通知 - 列表、未读数、标记已读
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.notification import (
    MarkReadBody,
    NotificationListResponse,
    NotificationResponse,
)
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False, description="仅未读"),
    type_filter: Optional[str] = Query(None, description="筛选类型: comment/reply/like/system"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """当前用户的通知列表（分页），含 total 与 unread_count。"""
    items, total = await notification_service.list_notifications(
        db, current_user.id, unread_only=unread_only, type_filter=type_filter, limit=limit, offset=offset
    )
    unread_count = await notification_service.get_unread_count(db, current_user.id)
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread_count,
    )


@router.get("/unread_count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """当前用户未读通知数量。"""
    count = await notification_service.get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.put("/read", response_model=dict)
async def mark_read(
    body: MarkReadBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记已读：body.notification_ids 为部分，body.all=true 为全部。"""
    if body.all:
        updated = await notification_service.mark_all_read(db, current_user.id)
    elif body.notification_ids:
        updated = await notification_service.mark_read(
            db, current_user.id, body.notification_ids
        )
    else:
        updated = 0
    # 统一返回类型为dict
    return {"updated": updated}


@router.put("/{notification_id}/read", response_model=dict)
async def mark_one_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """单条通知标记已读。"""
    ok = await notification_service.mark_one_read(
        db, current_user.id, notification_id
    )
    if not ok:
        return {"updated": 0}
    # 统一返回类型为dict，保持一致性
    return {"updated": 1}


@router.delete("")
async def delete_notifications(
    notification_ids: Optional[str] = Query(None, description="删除的通知ID列表，逗号分隔"),
    delete_all: bool = Query(False, description="删除全部通知"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除通知：可指定ID列表或全部删除。"""
    ids_list = None
    if notification_ids:
        ids_list = [id.strip() for id in notification_ids.split(",") if id.strip()]

    deleted = await notification_service.delete_notifications(
        db, current_user.id, notification_ids=ids_list, delete_all=delete_all
    )
    return {"deleted": deleted}
