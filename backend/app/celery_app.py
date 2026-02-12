"""
Celery 应用 - 技术方案 2.4 消息队列，Sprint 2.3 风控异步任务
broker/backend 使用 Redis，与 config 一致
"""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "payday",
    broker=settings.redis_url,
    backend=f"{settings.redis_url.replace('/0', '/1')}",
    include=["app.tasks.risk_check"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
