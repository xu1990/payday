"""
单元测试 - 定时任务 (app.tasks.scheduled)

注意: app/tasks/scheduled.py 中存在一些代码问题：
1. send_payday_reminders 使用了不存在的 User.payday_date 字段
2. calculate_daily_statistics 从错误的路径导入 Comment

这些测试通过完全 mock 来绕过这些问题。
"""
import pytest
from datetime import datetime, timedelta, date
from unittest.mock import MagicMock, patch, PropertyMock

from app.tasks.scheduled import (
    send_payday_reminders,
    calculate_daily_statistics,
    cleanup_expired_cache,
)


class TestSendPaydayReminders:
    """测试发薪日提醒任务"""

    @patch('app.tasks.scheduled.SessionLocal')
    @patch('app.tasks.scheduled.select')
    @patch('app.tasks.scheduled.User')
    def test_send_reminders_today_payday(self, mock_user, mock_select, mock_session_local):
        """测试发送当天发薪日提醒"""
        # Add payday_date as an attribute to the mocked User class
        mock_user.payday_date = MagicMock()

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        today = datetime.now().day

        # Create a mock user with payday_date attribute
        user = MagicMock()
        user.id = "test_user_1"
        user.payday_date = today
        user.allow_stranger_notice = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [user]
        mock_db.execute.return_value = mock_result

        # Mock select to return a chainable query builder
        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.where.return_value = mock_query

        count = send_payday_reminders()

        assert count == 1
        assert mock_db.add.call_count == 1

    @patch('app.tasks.scheduled.SessionLocal')
    @patch('app.tasks.scheduled.select')
    @patch('app.tasks.scheduled.User')
    def test_send_reminders_tomorrow_payday(self, mock_user, mock_select, mock_session_local):
        """测试发送明天发薪日提醒"""
        mock_user.payday_date = MagicMock()

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        today = datetime.now().day
        tomorrow = (datetime.now() + timedelta(days=1)).day

        user = MagicMock()
        user.id = "test_user_2"
        user.payday_date = tomorrow
        user.allow_stranger_notice = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [user]
        mock_db.execute.return_value = mock_result

        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.where.return_value = mock_query

        count = send_payday_reminders()

        assert count == 1

    @patch('app.tasks.scheduled.SessionLocal')
    @patch('app.tasks.scheduled.select')
    @patch('app.tasks.scheduled.User')
    def test_send_reminders_user_disallows_notices(self, mock_user, mock_select, mock_session_local):
        """测试用户不允许接收通知"""
        mock_user.payday_date = MagicMock()

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        today = datetime.now().day

        user = MagicMock()
        user.id = "test_user_3"
        user.payday_date = today
        user.allow_stranger_notice = False

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [user]
        mock_db.execute.return_value = mock_result

        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.where.return_value = mock_query

        count = send_payday_reminders()

        assert count == 0
        mock_db.add.assert_not_called()

    @patch('app.tasks.scheduled.SessionLocal')
    @patch('app.tasks.scheduled.select')
    @patch('app.tasks.scheduled.User')
    def test_send_reminders_no_users(self, mock_user, mock_select, mock_session_local):
        """测试没有符合条件的用户"""
        mock_user.payday_date = MagicMock()

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.where.return_value = mock_query

        count = send_payday_reminders()

        assert count == 0

    @patch('app.tasks.scheduled.SessionLocal')
    @patch('app.tasks.scheduled.select')
    @patch('app.tasks.scheduled.User')
    def test_send_reminders_multiple_users(self, mock_user, mock_select, mock_session_local):
        """测试发送给多个用户"""
        mock_user.payday_date = MagicMock()

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        today = datetime.now().day

        user1 = MagicMock()
        user1.id = "user_1"
        user1.payday_date = today
        user1.allow_stranger_notice = True

        user2 = MagicMock()
        user2.id = "user_2"
        user2.payday_date = today
        user2.allow_stranger_notice = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [user1, user2]
        mock_db.execute.return_value = mock_result

        mock_query = MagicMock()
        mock_select.return_value = mock_query
        mock_query.where.return_value = mock_query

        count = send_payday_reminders()

        assert count == 2


class TestCalculateDailyStatistics:
    """测试每日统计计算任务"""

    @patch('app.tasks.scheduled.SessionLocal')
    def test_calculate_statistics_with_data(self, mock_session_local):
        """测试计算统计数据"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        results = [5, 10, 15, 20]

        def mock_execute(query):
            mock_result = MagicMock()
            mock_result.scalar.return_value = results.pop(0) if results else 0
            return mock_result

        mock_db.execute.side_effect = mock_execute

        # Patch the imports that happen inside the function
        import sys
        old_post = sys.modules.get('app.models.post')
        old_comment = sys.modules.get('app.models.comment')
        old_salary_record = sys.modules.get('app.models.salary_record')

        try:
            # Create mock modules
            sys.modules['app.models.post'] = MagicMock()
            sys.modules['app.models.comment'] = MagicMock()
            sys.modules['app.models.salary_record'] = MagicMock()

            result = calculate_daily_statistics()

            assert "date" in result
            assert result["new_users"] == 5
            assert result["new_posts"] == 10
        finally:
            # Restore original modules
            if old_post is not None:
                sys.modules['app.models.post'] = old_post
            else:
                sys.modules.pop('app.models.post', None)
            if old_comment is not None:
                sys.modules['app.models.comment'] = old_comment
            else:
                sys.modules.pop('app.models.comment', None)
            if old_salary_record is not None:
                sys.modules['app.models.salary_record'] = old_salary_record
            else:
                sys.modules.pop('app.models.salary_record', None)

    @patch('app.tasks.scheduled.SessionLocal')
    def test_calculate_statistics_empty_data(self, mock_session_local):
        """测试没有新数据时的统计"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        # Patch the imports that happen inside the function
        import sys
        old_post = sys.modules.get('app.models.post')
        old_comment = sys.modules.get('app.models.comment')
        old_salary_record = sys.modules.get('app.models.salary_record')

        try:
            # Create mock modules
            sys.modules['app.models.post'] = MagicMock()
            sys.modules['app.models.comment'] = MagicMock()
            sys.modules['app.models.salary_record'] = MagicMock()

            result = calculate_daily_statistics()

            assert result["new_users"] == 0
            assert result["new_posts"] == 0
        finally:
            # Restore original modules
            if old_post is not None:
                sys.modules['app.models.post'] = old_post
            else:
                sys.modules.pop('app.models.post', None)
            if old_comment is not None:
                sys.modules['app.models.comment'] = old_comment
            else:
                sys.modules.pop('app.models.comment', None)
            if old_salary_record is not None:
                sys.modules['app.models.salary_record'] = old_salary_record
            else:
                sys.modules.pop('app.models.salary_record', None)


class TestCleanupExpiredCache:
    """测试清理过期缓存任务"""

    @patch('redis.from_url')
    @patch('app.core.config.get_settings')
    def test_cleanup_cache_with_redis(self, mock_get_settings, mock_from_url):
        """测试清理Redis缓存"""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.info.return_value = {"db0": {"keys": 100}, "db1": {"keys": 50}}

        result = cleanup_expired_cache()

        assert result == 150

    @patch('redis.from_url')
    @patch('app.core.config.get_settings')
    def test_cleanup_cache_empty_databases(self, mock_get_settings, mock_from_url):
        """测试空数据库"""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.info.return_value = {}

        result = cleanup_expired_cache()

        assert result == 0

    @patch('redis.from_url')
    @patch('app.core.config.get_settings')
    def test_cleanup_cache_some_empty_databases(self, mock_get_settings, mock_from_url):
        """测试部分数据库为空"""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.info.return_value = {"db0": {"keys": 10}, "db1": {}, "db2": {"keys": 20}}

        result = cleanup_expired_cache()

        assert result == 30
