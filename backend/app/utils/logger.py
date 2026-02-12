"""
日志工具 - 统一的日志配置
"""
import logging
import sys
from typing import Any

from app.core.config import get_settings

settings = get_settings()


def get_logger(name: str) -> logging.Logger:
    """
    获取配置好的 logger 实例

    Args:
        name: logger 名称，通常使用 __name__

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 设置日志级别
    log_level = logging.DEBUG if settings.debug else logging.INFO
    logger.setLevel(log_level)

    # 创建控制台 handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # 创建格式化器
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # 添加 handler
    logger.addHandler(handler)

    return logger
