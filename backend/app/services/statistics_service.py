"""
统计 - 本月汇总、简单趋势（如近 6 个月）；管理端仪表盘统计、数据洞察（Sprint 3.2）
"""
from datetime import date, datetime, time
from typing import Dict, List

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salary import SalaryRecord
from app.models.post import Post
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
    total = sum(decrypt_amount(r.amount_encrypted, r.encryption_salt) for r in records)
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


async def get_insights_distributions(db: AsyncSession) -> dict:
    """
    数据洞察 - 行业/城市/工资区间/发薪日分布（Sprint 3.2）
    统计所有已审核通过的帖子数据
    """
    # 基础查询：仅统计已审核通过的帖子
    base_query = (
        select(Post)
        .where(Post.status == "normal", Post.risk_status == "approved")
    )

    # 行业分布（Top 10）
    industry_result = await db.execute(
        select(Post.industry, func.count().label("count"))
        .where(Post.status == "normal", Post.risk_status == "approved")
        .where(Post.industry.isnot(None))
        .group_by(Post.industry)
        .order_by(func.count().desc())
        .limit(10)
    )
    industry_dist = [
        {"label": r[0] or "未知", "value": r[1]}
        for r in industry_result.all()
    ]

    # 城市分布（Top 10）
    city_result = await db.execute(
        select(Post.city, func.count().label("count"))
        .where(Post.status == "normal", Post.risk_status == "approved")
        .where(Post.city.isnot(None))
        .group_by(Post.city)
        .order_by(func.count().desc())
        .limit(10)
    )
    city_dist = [
        {"label": r[0] or "未知", "value": r[1]}
        for r in city_result.all()
    ]

    # 工资区间分布
    salary_ranges = {
        "0-3K": 0,
        "3-5K": 0,
        "5-10K": 0,
        "10-15K": 0,
        "15-20K": 0,
        "20K+": 0,
    }

    # 获取所有工资记录进行区间统计
    all_salaries = await db.execute(
        select(SalaryRecord.amount_encrypted, SalaryRecord.encryption_salt)
        .where(SalaryRecord.payday_date.isnot(None))
    )
    salaries = [
        decrypt_amount(r.amount_encrypted, r.encryption_salt) / 1000  # 转换为K
        for r in all_salaries.all()
    ]

    for salary_k in salaries:
        if salary_k < 3:
            salary_ranges["0-3K"] += 1
        elif salary_k < 5:
            salary_ranges["3-5K"] += 1
        elif salary_k < 10:
            salary_ranges["5-10K"] += 1
        elif salary_k < 15:
            salary_ranges["10-15K"] += 1
        elif salary_k < 20:
            salary_ranges["15-20K"] += 1
        else:
            salary_ranges["20K+"] += 1

    salary_range_dist = [
        {"label": k, "value": v}
        for k, v in salary_ranges.items()
    ]

    # 发薪日分布（每月1-31号）
    from app.models.payday import PaydayConfig
    payday_result = await db.execute(
        select(func.count().label("count"), PaydayConfig.payday)
        .join(User, PaydayConfig.user_id == User.id)
        .where(PaydayConfig.calendar_type == "solar")
        .group_by(PaydayConfig.payday)
        .order_by(PaydayConfig.payday)
    )

    payday_dist = [{"label": f"{r[1]}号", "value": r[0]} for r in payday_result.all()]

    total_posts = await db.execute(
        select(func.count()).select_from(Post).where(
            Post.status == "normal", Post.risk_status == "approved"
        )
    )

    return {
        "industry_distribution": {
            "total": len(industry_dist),
            "data": industry_dist,
        },
        "city_distribution": {
            "total": len(city_dist),
            "data": city_dist,
        },
        "salary_range_distribution": {
            "total": sum(salary_ranges.values()),
            "data": salary_range_dist,
        },
        "payday_distribution": {
            "total": len(payday_dist),
            "data": payday_dist,
        },
        "total_posts": total_posts.scalar() or 0,
    }
