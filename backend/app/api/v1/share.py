"""
分享接口 - P1-2 分享功能
创建分享记录、查询分享状态、获取分享统计
"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.share import ShareCreate, ShareResponse, ShareStatsResponse
from app.services.share_service import (
    create_share,
    update_share_status,
    get_user_shares,
    get_share_stats,
)

router = APIRouter(prefix="/share", tags=["share"])


@router.post("", response_model=ShareResponse)
async def create_share_endpoint(
    data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建分享记录"""
    share = await create_share(
        db,
        user_id=current_user.id,
        target_type=data.target_type,
        target_id=data.target_id,
        share_channel=data.share_channel,
    )
    return ShareResponse.model_validate(share)


@router.get("", response_model=list[ShareResponse])
async def list_shares(
    current_user: User = Depends(get_current_user),
    target_type: Optional[str] = Query(None, description="筛选分享目标类型"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的分享记录"""
    shares, total = await get_user_shares(
        db,
        user_id=current_user.id,
        target_type=target_type,
        limit=limit,
        offset=offset,
    )
    return {"items": [ShareResponse.model_validate(s) for s in shares], "total": total}


@router.get("/stats", response_model=ShareStatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=30, description="统计最近N天"),
    db: AsyncSession = Depends(get_db),
):
    """获取分享统计（最近N天的分享次数、成功率）"""
    stats = await get_share_stats(db, current_user.id, days)
    return stats


@router.put("/{share_id}/status", response_model=ShareResponse)
async def update_status(
    share_id: str,
    data: ShareUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新分享状态（通常由前端回调更新）"""
    share = await update_share_status(
        db,
        share_id=share_id,
        status=data.status,
        error_message=data.error_message,
    )
    if not share:
        raise HTTPException(status_code=404, detail="分享记录不存在")
    return ShareResponse.model_validate(share)
