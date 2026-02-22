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


async def get_year_end_bonus_stats(db: AsyncSession, year: int = None) -> dict:
    """
    年终奖统计（Sprint 4.2）
    按年份统计年终奖数据
    """
    # 查询年终奖记录 (salary_type='bonus')
    query = select(SalaryRecord).where(SalaryRecord.salary_type == "bonus")

    # 如果指定年份，过滤该年份的记录
    if year:
        query = query.where(func.extract('year', SalaryRecord.payday_date) == year)

    result = await db.execute(query)
    bonus_records = result.scalars().all()

    # 解密并统计数据
    amounts = [
        decrypt_amount(r.amount_encrypted, r.encryption_salt)
        for r in bonus_records
    ]

    if not amounts:
        return {
            "year": year,
            "total_count": 0,
            "total_amount": 0,
            "average_amount": 0,
            "median_amount": 0,
            "max_amount": 0,
            "min_amount": 0,
            "ranges": {
                "0-5K": 0,
                "5-10K": 0,
                "10-20K": 0,
                "20-50K": 0,
                "50K+": 0,
            },
        }

    total_count = len(amounts)
    total_amount = sum(amounts)
    average_amount = total_amount / total_count
    max_amount = max(amounts)
    min_amount = min(amounts)

    # 计算中位数
    sorted_amounts = sorted(amounts)
    median_amount = sorted_amounts[total_count // 2] if total_count % 2 == 1 else (
        sorted_amounts[total_count // 2 - 1] + sorted_amounts[total_count // 2]
    ) / 2

    # 区间分布
    ranges = {
        "0-5K": sum(1 for a in amounts if a < 5000),
        "5-10K": sum(1 for a in amounts if 5000 <= a < 10000),
        "10-20K": sum(1 for a in amounts if 10000 <= a < 20000),
        "20-50K": sum(1 for a in amounts if 20000 <= a < 50000),
        "50K+": sum(1 for a in amounts if a >= 50000),
    }

    return {
        "year": year,
        "total_count": total_count,
        "total_amount": round(total_amount, 2),
        "average_amount": round(average_amount, 2),
        "median_amount": round(median_amount, 2),
        "max_amount": round(max_amount, 2),
        "min_amount": round(min_amount, 2),
        "ranges": ranges,
    }


async def get_ontime_payment_stats(db: AsyncSession, year: int = None) -> dict:
    """
    准时发薪统计（Sprint 4.3）
    统计准时发薪、拖欠工资的情况
    """
    # 构建查询
    query = select(SalaryRecord).where(SalaryRecord.salary_type == "normal")

    if year:
        query = query.where(func.extract('year', SalaryRecord.payday_date) == year)

    result = await db.execute(query)
    records = result.scalars().all()

    if not records:
        return {
            "year": year,
            "total_count": 0,
            "ontime_count": 0,
            "ontime_rate": 0,
            "arrears_count": 0,
            "arrears_rate": 0,
            "avg_delayed_days": 0,
        }

    total_count = len(records)

    # 准时发薪（is_arrears=0 或 is_arrears is null，且 delayed_days is null 或 = 0）
    ontime_records = [r for r in records if (r.is_arrears or 0) == 0 and ((r.delayed_days or 0) == 0)]
    ontime_count = len(ontime_records)

    # 拖欠记录
    arrears_records = [r for r in records if (r.is_arrears or 0) == 1 or ((r.delayed_days or 0) > 0)]
    arrears_count = len(arrears_records)

    # 平均延迟天数
    delayed_days_list = [r.delayed_days for r in records if r.delayed_days and r.delayed_days > 0]
    avg_delayed_days = sum(delayed_days_list) / len(delayed_days_list) if delayed_days_list else 0

    return {
        "year": year,
        "total_count": total_count,
        "ontime_count": ontime_count,
        "ontime_rate": round(ontime_count / total_count * 100, 2) if total_count > 0 else 0,
        "arrears_count": arrears_count,
        "arrears_rate": round(arrears_count / total_count * 100, 2) if total_count > 0 else 0,
        "avg_delayed_days": round(avg_delayed_days, 2),
    }
