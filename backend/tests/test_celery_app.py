"""
单元测试 - Celery 应用配置 (app.celery_app)

Note: This test file needs the real celery module, not the mock in tests/api/conftest.py
So we restore the real celery before importing app.celery_app
"""
import sys
import pytest
from unittest.mock import patch, MagicMock

# Restore real celery module (undo the mock from tests/api/conftest.py)
if 'celery' in sys.modules and isinstance(sys.modules['celery'], MagicMock):
    sys.modules.pop('celery', None)

from app.celery_app import celery_app


class TestCeleryApp:
    """测试 Celery 应用配置"""

    def test_celery_app_exists(self):
        """测试 Celery 应用存在"""
        assert celery_app is not None
        assert celery_app.main == "payday"

    def test_celery_app_broker_url(self):
        """测试 Celery broker URL 配置"""
        # Broker URL 在 conf.broker_url 中
        assert celery_app.conf.broker_url is not None
        assert "redis" in celery_app.conf.broker_url.lower()

    def test_celery_app_backend_url(self):
        """测试 Celery backend URL 配置"""
        # Backend URL 应该使用不同的 redis db
        assert celery_app.conf.result_backend is not None
        assert "redis" in celery_app.conf.result_backend.lower()

    def test_celery_app_includes_tasks(self):
        """测试 Celery 包含的任务模块"""
        expected_tasks = ["app.tasks.risk_check", "app.tasks.scheduled"]
        for task in expected_tasks:
            assert task in celery_app.conf.include

    def test_celery_beat_schedule_exists(self):
        """测试 Celery Beat 调度配置存在"""
        assert hasattr(celery_app.conf, 'beat_schedule')
        assert isinstance(celery_app.conf.beat_schedule, dict)

    def test_celery_beat_schedule_tasks(self):
        """测试 Celery Beat 调度任务"""
        schedule = celery_app.conf.beat_schedule

        # 验证预期的定时任务存在
        expected_tasks = [
            "send-payday-reminders",
            "calculate-daily-statistics",
            "cleanup-expired-cache",
        ]

        for task in expected_tasks:
            assert task in schedule
            assert 'task' in schedule[task]
            assert 'schedule' in schedule[task]

    def test_celery_beat_schedule_payday_reminders(self):
        """测试发薪日提醒任务配置"""
        schedule = celery_app.conf.beat_schedule
        task = schedule.get("send-payday-reminders")

        assert task is not None
        assert task['task'] == "tasks.send_payday_reminders"
        # 验证是 crontab 调度
        from celery.schedules import crontab
        assert isinstance(task['schedule'], crontab)
        # 检查 crontab 属性（不同版本的 celery 可能有不同的属性名）
        assert hasattr(task['schedule'], '_hour') or hasattr(task['schedule'], 'hour')

    def test_celery_beat_schedule_statistics(self):
        """测试统计计算任务配置"""
        schedule = celery_app.conf.beat_schedule
        task = schedule.get("calculate-daily-statistics")

        assert task is not None
        assert task['task'] == "tasks.calculate_daily_statistics"
        from celery.schedules import crontab
        assert isinstance(task['schedule'], crontab)
        assert hasattr(task['schedule'], '_hour') or hasattr(task['schedule'], 'hour')

    def test_celery_beat_schedule_cleanup_cache(self):
        """测试缓存清理任务配置"""
        schedule = celery_app.conf.beat_schedule
        task = schedule.get("cleanup-expired-cache")

        assert task is not None
        assert task['task'] == "tasks.cleanup_expired_cache"
        from celery.schedules import crontab
        assert isinstance(task['schedule'], crontab)

    def test_celery_serializer_config(self):
        """测试 Celery 序列化配置"""
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.accept_content == ["json"]
        assert celery_app.conf.result_serializer == "json"

    def test_celery_timezone_config(self):
        """测试 Celery 时区配置"""
        assert celery_app.conf.timezone == "Asia/Shanghai"
        assert celery_app.conf.enable_utc is True

    def test_celery_worker_config(self):
        """测试 Celery worker 配置"""
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_reject_on_worker_lost is True
        assert celery_app.conf.worker_prefetch_multiplier == 4
        assert celery_app.conf.worker_max_tasks_per_child == 1000

    def test_celery_conf_values(self):
        """测试 Celery 配置值正确设置"""
        # 验证配置是通过 update 方法设置的
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.timezone == "Asia/Shanghai"
        assert celery_app.conf.worker_prefetch_multiplier == 4
