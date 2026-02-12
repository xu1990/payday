"""
统计 - 本月汇总、简单趋势、数据洞察（Sprint 3.2）
"""
from datetime import date
from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.statistics_service import get_month_summary, get_trend, get_insights_distributions
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/summary")
async def statistics_summary(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_month_summary(db, current_user.id, year, month)


@router.get("/trend")
async def statistics_trend(
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_trend(db, current_user.id, months)


@router.get("/insights")
async def statistics_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    数据洞察 - 行业/城市/工资区间/发薪日分布
    与 PRD 数据洞察一致，Sprint 3.2
    """
    return await get_insights_distributions(db)
