"""
打卡接口 - 打卡、连续天数统计、日历；Sprint 3.3
"""
from datetime import date
from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.checkin import CheckInCreate, CheckInCalendarResponse, CheckInStatsResponse
from app.services.checkin_service import (
    check_in,
    get_checkin_calendar,
    get_checkin_stats,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("", response_model=dict)
async def create_checkin(
    body: CheckInCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """打卡"""
    checkin = await check_in(db, current_user.id, body.check_date, body.note)
    return {
        "id": checkin.id,
        "check_date": checkin.check_date.isoformat(),
        "note": checkin.note,
    }


@router.get("/calendar")
async def checkin_calendar(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取某月的打卡日历"""
    items = await get_checkin_calendar(db, current_user.id, year, month)
    return CheckInCalendarResponse(items=items)


@router.get("/stats")
async def checkin_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户打卡统计：总天数、本月天数、当前连续天数"""
    stats = await get_checkin_stats(db, current_user.id)
    return CheckInStatsResponse(
        total_days=stats["total_days"],
        this_month=stats["this_month"],
        current_streak=stats["current_streak"],
    )
