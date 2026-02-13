"""
日期时间工具模块
"""
from datetime import datetime
from typing import Optional


def now(tz: Optional[str] = None) -> datetime:
    """
    获取当前时间

    Args:
        tz: 时区（暂未实现）

    Returns:
        当前UTC时间的datetime对象
    """
    return datetime.utcnow()
