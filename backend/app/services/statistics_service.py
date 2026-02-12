"""
统计 - 本月汇总、简单趋势（如近 6 个月）；管理端仪表盘统计
"""
from datetime import date, datetime, time
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salary import SalaryRecord
from app.models.user import User
from app.utils.encryption import decrypt_amount


async def get_month_summary(db: AsyncSession, user_id: str, year: int, month: int) -> dict:
    from_date = date(year, month, 1)
    if month == 12:
        to_date = date(year, 12, 31)
    else:
        to_date = date(year, month + 1, 1)
        from datetime import timedelta
        to_date = to_date - timedelta(days=1)
    result = await db.execute(
        select(SalaryRecord).where(
            SalaryRecord.user_id == user_id,
            SalaryRecord.payday_date >= from_date,
            SalaryRecord.payday_date <= to_date,
        )
    )
    records = list(result.scalars().all())
    total = sum(decrypt_amount(r.amount_encrypted) for r in records)
    count = len(records)
    return {"year": year, "month": month, "total_amount": round(total, 2), "record_count": count}


async def get_trend(
    db: AsyncSession, user_id: str, months: int = 6
) -> list[dict]:
    """近 months 个月每月汇总（按自然月）"""
    today = date.today()
    out = []
    for i in range(months):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        summary = await get_month_summary(db, user_id, y, m)
        out.append(summary)
    return out


def _today_start_utc() -> datetime:
    """今日 0 点 UTC（naive，与 models 的 datetime.utcnow 一致）"""
    d = datetime.utcnow().date()
    return datetime.combine(d, time.min)


async def get_admin_dashboard_stats(db: AsyncSession) -> dict:
    """管理端：用户总数、今日新增用户、工资记录总数、今日新增记录"""
    today_start = _today_start_utc()
    user_total_r = await db.execute(select(func.count()).select_from(User))
    user_new_today_r = await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    )
    salary_total_r = await db.execute(select(func.count()).select_from(SalaryRecord))
    salary_today_r = await db.execute(
        select(func.count()).select_from(SalaryRecord).where(
            SalaryRecord.created_at >= today_start
        )
    )
    return {
        "user_total": user_total_r.scalar() or 0,
        "user_new_today": user_new_today_r.scalar() or 0,
        "salary_record_total": salary_total_r.scalar() or 0,
        "salary_record_today": salary_today_r.scalar() or 0,
    }
