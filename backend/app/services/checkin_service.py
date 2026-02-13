"""
打卡服务 - 连续打卡统计、日历展示；Sprint 3.3
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin import CheckIn
from app.models.user import User


async def get_user_checkin_streak(db: AsyncSession, user_id: str) -> int:
    """获取用户当前连续打卡天数"""
    # 查询最近一次打卡记录
    latest = await db.execute(
        select(CheckIn)
        .where(CheckIn.user_id == user_id)
        .order_by(CheckIn.check_date.desc())
        .limit(1)
    )
    latest_checkin = latest.scalar_one_or_none()
    if not latest_checkin:
        return 0

    # 计算从最后一次打卡开始连续的天数
    check_date = latest_checkin.check_date
    streak = 1  # 包括最后一次打卡

    while True:
        prev_date = check_date - timedelta(days=1)
        # 查询前一天是否有打卡
        prev = await db.execute(
            select(CheckIn)
            .where(CheckIn.user_id == user_id, CheckIn.check_date == prev_date)
        )
        if not prev.scalar_one_or_none():
            break  # 没有打卡，连续中断
        streak += 1
        check_date = prev_date

        # 最多查询365天
        if streak >= 365:
            break

    return streak


async def check_in(
    db: AsyncSession,
    user_id: str,
    check_date: date,
    note: Optional[str] = None,
) -> CheckIn:
    """打卡"""
    checkin = CheckIn(
        user_id=user_id,
        check_date=check_date,
        note=note or "",
    )
    db.add(checkin)
    await db.commit()
    await db.refresh(checkin)
    return checkin


async def get_checkin_calendar(
    db: AsyncSession,
    user_id: str,
    year: int,
    month: int,
) -> List[dict]:
    """获取某月的打卡日历（返回已打卡日期列表）"""
    from_date = date(year, month, 1)
    if month == 12:
        to_date = date(year, 12, 31)
    else:
        to_date = date(year, month + 1, 1)
        from datetime import timedelta
        to_date = to_date - timedelta(days=1)

    result = await db.execute(
        select(CheckIn.check_date)
        .where(
            CheckIn.user_id == user_id,
            CheckIn.check_date >= from_date,
            CheckIn.check_date <= to_date,
        )
        .order_by(CheckIn.check_date)
    )

    # result.scalars() returns date objects directly since we selected check_date
    return [
        {"date": r.isoformat()}
        for r in result.scalars().all()
    ]


async def get_checkin_stats(db: AsyncSession, user_id: str) -> dict:
    """获取用户打卡统计：总天数、本月天数、当前连续天数"""
    today = date.today()

    # 总打卡天数
    total_days = await db.execute(
        select(func.count()).select_from(CheckIn).where(CheckIn.user_id == user_id)
    )
    total = total_days.scalar() or 0

    # 本月打卡天数
    month_start = date(today.year, today.month, 1)
    month_days = await db.execute(
        select(func.count())
        .select_from(CheckIn)
        .where(CheckIn.user_id == user_id, CheckIn.check_date >= month_start)
    )
    this_month = month_days.scalar() or 0

    # 当前连续天数
    streak = await get_user_checkin_streak(db, user_id)

    return {
        "total_days": total,
        "this_month": this_month,
        "current_streak": streak,
    }
