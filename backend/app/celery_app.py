"""
Celery 应用 - 技术方案 2.4 消息队列，Sprint 2.3 风控异步任务
broker/backend 使用 Redis，与 config 一致
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "payday",
    broker=settings.redis_url,
    backend=f"{settings.redis_url.replace('/0', '/1')}",
    include=["app.tasks.risk_check", "app.tasks.scheduled"],
)

# Celery Beat 定时任务配置
celery_app.conf.beat_schedule = {
    # 发薪日提醒 - 每天早上 8:00 执行
    "send-payday-reminders": {
        "task": "tasks.send_payday_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    # 统计数据计算 - 每天凌晨 1:00 执行
    "calculate-daily-statistics": {
        "task": "tasks.calculate_daily_statistics",
        "schedule": crontab(hour=1, minute=0),
    },
    # 清理过期缓存 - 每小时执行一次
    "cleanup-expired-cache": {
        "task": "tasks.cleanup_expired_cache",
        "schedule": crontab(minute=0),
    },
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)
