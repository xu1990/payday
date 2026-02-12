"""
结构化日志工具 - 使用JSON格式和上下文信息
支持日志轮转、分级过滤和结构化查询
"""
import logging
import sys
import json
import threading
from typing import Any, Optional, Dict
from pathlib import Path
from app.core.config import get_settings

settings = get_settings()

# 线程本地存储，用于传递上下文信息（如request_id）
_log_context = threading.local()


class StructuredLogger:
    """
    结构化日志器 - 支持JSON格式、上下文信息和额外字段
    """

    def __init__(self, name: str):
        """
        初始化结构化日志器

        Args:
            name: logger名称，通常使用__name__
        """
        self.name = name
        self.logger = logging.getLogger(name)

    def _format_log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """
        格式化日志消息为JSON结构

        Args:
            level: 日志级别
            message: 日志消息
            extra: 额外的上下文字段

        Returns:
            JSON格式的日志字符串
        """
        log_entry = {
            "timestamp": self.get_timestamp(),
            "level": logging.getLevelName(level),
            "logger": self.name,
            "message": message,
            "environment": settings.environment,
        }

        # 添加线程本地存储的上下文信息（request_id、user_id等）
        if hasattr(_log_context, 'get'):
            context = _log_context.get()
            if context:
                for key, value in context.items():
                    if key not in log_entry:
                        log_entry[key] = value

        # 添加额外字段
        if extra:
            log_entry.update(extra)

        return json.dumps(log_entry, ensure_ascii=False)

    def get_timestamp(self) -> str:
        """
        获取ISO 8601格式的时间戳

        Returns:
            ISO 8601格式的时间字符串
        """
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def _add_context_fields(self, **kwargs) -> Dict[str, Any]:
        """
        添加上下文字段到日志记录

        Returns:
            包含上下文字段的字典
        """
        return kwargs

    def debug(self, message: str, **kwargs):
        """DEBUG级别日志"""
        extra = self._add_context_fields(**kwargs)
        self.logger.debug(message, extra=extra)

    def info(self, message: str, **kwargs):
        """INFO级别日志"""
        extra = self._add_context_fields(**kwargs)
        self.logger.info(message, extra=extra)

    def warning(self, message: str, **kwargs):
        """WARNING级别日志"""
        extra = self._add_context_fields(**kwargs)
        self.logger.warning(message, extra=extra)

    def error(self, message: str, **kwargs):
        """ERROR级别日志"""
        extra = self._add_context_fields(**kwargs)
        self.logger.error(message, extra=extra)

    def critical(self, message: str, **kwargs):
        """CRITICAL级别日志"""
        extra = self._add_context_fields(**kwargs)
        self.logger.critical(message, extra=extra)

    def exception(self, message: str, exc_info: bool = True, **kwargs):
        """
        记录异常信息

        Args:
            message: 错误消息
            exc_info: 是否包含异常堆栈信息
            **kwargs: 额外上下文字段
        """
        extra = self._add_context_fields(**kwargs)
        self.logger.exception(message, exc_info=exc_info, extra=extra)


def set_log_context(**kwargs) -> None:
    """
    设置线程本地存储的日志上下文

    Args:
        **kwargs: 上下文字段（如request_id、user_id等）

    Example:
        set_log_context(request_id='123-456', user_id='user-001')
    """
    _log_context.update(kwargs)


def clear_log_context() -> None:
    """
    清除线程本地存储的日志上下文

    通常在请求结束后调用
    """
    if hasattr(_log_context, 'clear'):
        _log_context.clear()


def get_logger(name: str) -> StructuredLogger:
    """
    获取结构化日志器实例

    Args:
        name: logger名称，通常使用__name__

    Returns:
        配置好的StructuredLogger实例

    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", user_id="123")
    """
    return StructuredLogger(name)


def setup_json_handler(filename: Optional[str] = None) -> logging.Handler:
    """
    设置JSON格式化handler，用于输出到文件

    Args:
        filename: 日志文件路径，None表示只输出到控制台

    Returns:
            配置好的logging.Handler
    """
    if filename:
        # 确保日志目录存在
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        class JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_obj = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                # 添加extra字段
                if hasattr(record, '__dict__'):
                    log_obj.update(record.__dict__)
                return json.dumps(log_obj, ensure_ascii=False)

            def formatTime(self, record: logging.LogRecord) -> str:
                from datetime import datetime
                return datetime.fromtimestamp(record.created).strftime("%Y-%m-%dT%H:%M:%SZ")

        handler = logging.FileHandler(
            filename=filename,
            encoding='utf-8'
        )
        handler.setFormatter(JsonFormatter())
    else:
        # 控制台输出也使用JSON格式
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())

    return handler


def configure_logging(log_file: Optional[str] = None, log_level: str = None):
    """
    配置全局日志设置

    Args:
        log_file: 日志文件路径（可选）
        log_level: 日志级别字符串（DEBUG/INFO/WARNING/ERROR）

    Example:
        configure_logging(log_file='logs/app.log', log_level='INFO')
    """
    # 设置根logger的日志级别
    level = getattr(logging, log_level.upper() if log_level else logging.INFO)

    # 配置handler
    handlers = [setup_json_handler(log_file)]

    # 配置根logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )
