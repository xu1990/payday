"""
通知 - 列表、未读数、标记已读
"""
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
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """当前用户的通知列表（分页），含 total 与 unread_count。"""
    items, total = await notification_service.list_notifications(
        db, current_user.id, unread_only=unread_only, limit=limit, offset=offset
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


@router.put("/read")
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
    return {"updated": updated}


@router.put("/{notification_id}/read")
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
    return {"updated": 1}
