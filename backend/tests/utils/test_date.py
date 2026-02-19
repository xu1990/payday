"""测试日期工具"""
import pytest
from datetime import datetime
from app.utils.date import now


class TestNow:
    """测试获取当前时间"""

    def test_now_returns_datetime(self):
        """测试返回datetime对象"""
        result = now()
        assert isinstance(result, datetime)

    def test_now_is_utc(self):
        """测试返回UTC时间"""
        result = now()
        # now()返回UTC时间，可能与时区有差异，但应该是最近的时间
        import time
        from datetime import datetime
        current_utc = datetime.utcnow()
        time_diff = abs((current_utc - result).total_seconds())
        # 允许1秒误差
        assert time_diff < 1

    def test_now_no_tz_parameter(self):
        """测试不带时区参数"""
        result = now()
        assert isinstance(result, datetime)
        # tz参数暂未实现，但不应报错

    def test_now_with_none_tz(self):
        """测试tz=None"""
        result = now(tz=None)
        assert isinstance(result, datetime)
