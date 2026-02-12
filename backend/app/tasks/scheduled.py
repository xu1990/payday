"""
定时任务 - 发薪日提醒、统计数据计算等
使用 Celery Beat 调度
"""
from celery import shared_task
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.user import User
from app.models.notification import Notification
from sqlalchemy import select


@shared_task(name="tasks.send_payday_reminders")
def send_payday_reminders() -> int:
    """
    发送发薪日提醒
    每天早上 8:00 执行，提醒当天或明天发薪的用户
    """
    db = SessionLocal()
    try:
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        # 查询今天或明天发薪的用户
        result = db.execute(
            select(User).where(
                (User.payday_date == today.day) | (User.payday_date == tomorrow.day)
            )
        )
        users = result.scalars().all()

        count = 0
        for user in users:
            if not user.allow_stranger_notice:
                continue

            payday_day = user.payday_date
            if payday_day == today.day:
                title = "今天是发薪日！"
                content = "发薪日快乐！记得记录今天的工资情况~"
            else:
                title = "明天是发薪日"
                content = "明天就是发薪日了，记得记录工资情况哦~"

            notification = Notification(
                user_id=user.id,
                type="system",
                title=title,
                content=content,
            )
            db.add(notification)
            count += 1

        db.commit()
        return count

    finally:
        db.close()


@shared_task(name="tasks.calculate_daily_statistics")
def calculate_daily_statistics() -> dict:
    """
    计算每日统计数据
    每天凌晨 1:00 执行
    """
    db = SessionLocal()
    try:
        # 统计今日新增用户数
        today = datetime.now().date()
        from app.models.post import Post, Comment, SalaryRecord
        from sqlalchemy import func

        new_users_count = db.execute(
            select(func.count(User.id)).where(
                func.date(User.created_at) == today
            )
        ).scalar() or 0

        # 统计今日新增帖子数
        new_posts_count = db.execute(
            select(func.count(Post.id)).where(
                func.date(Post.created_at) == today
            )
        ).scalar() or 0

        # 统计今日新增评论数
        new_comments_count = db.execute(
            select(func.count(Comment.id)).where(
                func.date(Comment.created_at) == today
            )
        ).scalar() or 0

        # 统计今日新增工资记录数
        new_salary_records_count = db.execute(
            select(func.count(SalaryRecord.id)).where(
                func.date(SalaryRecord.created_at) == today
            )
        ).scalar() or 0

        return {
            "date": today.isoformat(),
            "new_users": new_users_count,
            "new_posts": new_posts_count,
            "new_comments": new_comments_count,
            "new_salary_records": new_salary_records_count,
        }

    finally:
        db.close()


@shared_task(name="tasks.cleanup_expired_cache")
def cleanup_expired_cache() -> int:
    """
    清理过期缓存
    每小时执行一次
    """
    import redis
    from app.core.config import get_settings

    settings = get_settings()
    r = redis.from_url(settings.redis_url)

    # 统计 Redis 键数量（实际清理由 Redis 自动过期处理）
    info = r.info("keyspace")

    # 返回数据库键数量
    total_keys = sum(db_stats.get("keys", 0) for db_stats in info.values())

    return total_keys
