"""
单元测试 - 结构化日志工具 (app.utils.logger_v2)
"""
import pytest
import logging
import json
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import os

from app.utils.logger_v2 import (
    StructuredLogger,
    set_log_context,
    clear_log_context,
    get_logger,
    setup_json_handler,
    configure_logging,
    _log_context,
)


class TestStructuredLogger:
    """测试StructuredLogger类"""

    def test_init(self):
        """测试初始化"""
        logger = StructuredLogger("test_logger")
        assert logger.name == "test_logger"
        assert logger.logger.name == "test_logger"

    def test_get_timestamp(self):
        """测试获取时间戳"""
        logger = StructuredLogger("test_logger")
        timestamp = logger.get_timestamp()
        assert isinstance(timestamp, str)
        assert "T" in timestamp
        assert "Z" in timestamp

    def test_add_context_fields(self):
        """测试添加上下文字段"""
        logger = StructuredLogger("test_logger")
        result = logger._add_context_fields(user_id="123", action="test")
        assert result == {"user_id": "123", "action": "test"}

    def test_add_context_fields_empty(self):
        """测试空上下文字段"""
        logger = StructuredLogger("test_logger")
        result = logger._add_context_fields()
        assert result == {}

    @patch('app.utils.logger_v2.settings')
    def test_format_log_basic(self, mock_settings):
        """测试基本日志格式化"""
        mock_settings.environment = "test"
        logger = StructuredLogger("test_logger")

        result = logger._format_log(logging.INFO, "Test message")

        log_data = json.loads(result)
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["environment"] == "test"
        assert "timestamp" in log_data

    @patch('app.utils.logger_v2.settings')
    def test_format_log_with_extra(self, mock_settings):
        """测试带额外字段的日志格式化"""
        mock_settings.environment = "test"
        logger = StructuredLogger("test_logger")

        result = logger._format_log(
            logging.INFO,
            "Test message",
            extra={"user_id": "123", "action": "login"}
        )

        log_data = json.loads(result)
        assert log_data["user_id"] == "123"
        assert log_data["action"] == "login"

    @patch('app.utils.logger_v2.settings')
    @patch('app.utils.logger_v2._log_context')
    def test_format_log_with_context(self, mock_context, mock_settings):
        """测试带线程上下文的日志格式化"""
        mock_settings.environment = "test"
        mock_context.get.return_value = {"request_id": "abc-123"}

        logger = StructuredLogger("test_logger")
        result = logger._format_log(logging.INFO, "Test message")

        log_data = json.loads(result)
        assert log_data["request_id"] == "abc-123"

    def test_debug_logging(self):
        """测试DEBUG级别日志"""
        logger = StructuredLogger("test_logger")
        # Just verify it doesn't crash
        logger.debug("Debug message", test_key="test_value")

    def test_info_logging(self):
        """测试INFO级别日志"""
        logger = StructuredLogger("test_logger")
        logger.info("Info message", test_key="test_value")

    def test_warning_logging(self):
        """测试WARNING级别日志"""
        logger = StructuredLogger("test_logger")
        logger.warning("Warning message", test_key="test_value")

    def test_error_logging(self):
        """测试ERROR级别日志"""
        logger = StructuredLogger("test_logger")
        logger.error("Error message", test_key="test_value")

    def test_critical_logging(self):
        """测试CRITICAL级别日志"""
        logger = StructuredLogger("test_logger")
        logger.critical("Critical message", test_key="test_value")

    def test_exception_logging(self):
        """测试异常日志"""
        logger = StructuredLogger("test_logger")
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Exception occurred", test_key="test_value")

    def test_exception_logging_without_exc_info(self):
        """测试异常日志不包含堆栈"""
        logger = StructuredLogger("test_logger")
        logger.exception("Exception occurred", exc_info=False, test_key="test_value")


class TestLogContext:
    """测试日志上下文管理"""

    def test_set_log_context(self):
        """测试设置日志上下文"""
        # 清除可能存在的上下文
        if hasattr(_log_context, 'clear'):
            _log_context.clear()

        set_log_context(request_id="test-123", user_id="user-001")

        # 验证上下文已设置
        context = _log_context.get()
        assert context["request_id"] == "test-123"
        assert context["user_id"] == "user-001"

    def test_clear_log_context(self):
        """测试清除日志上下文"""
        set_log_context(request_id="test-123")
        clear_log_context()

        # 验证上下文已清除
        context = _log_context.get()
        assert context == {}


class TestGetLogger:
    """测试get_logger函数"""

    def test_get_logger_returns_instance(self):
        """测试get_logger返回StructuredLogger实例"""
        logger = get_logger("test.module")
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test.module"

    def test_get_logger_same_name_same_instance(self):
        """测试相同名称返回相同logger实例（通过logging模块）"""
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")
        # 应该返回相同的底层logger
        assert logger1.logger is logger2.logger


class TestSetupJsonHandler:
    """测试setup_json_handler函数"""

    def test_setup_console_handler(self):
        """测试设置控制台handler"""
        handler = setup_json_handler(None)

        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream.name == "<stdout>"

    def test_setup_file_handler(self):
        """测试设置文件handler"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")

            handler = setup_json_handler(log_file)

            assert isinstance(handler, logging.FileHandler)
            # 验证文件被创建
            assert os.path.exists(log_file)

    def test_setup_file_handler_creates_directory(self):
        """测试文件handler创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "logs", "nested", "test.log")

            handler = setup_json_handler(log_file)

            # 验证目录被创建
            assert os.path.exists(os.path.dirname(log_file))


class TestConfigureLogging:
    """测试configure_logging函数"""

    @patch('app.utils.logger_v2.setup_json_handler')
    @patch('app.utils.logger_v2.logging.basicConfig')
    def test_configure_logging_basic(self, mock_basicConfig, mock_handler):
        """测试基本日志配置"""
        mock_handler.return_value = MagicMock()

        configure_logging()

        # 验证basicConfig被调用
        mock_basicConfig.assert_called_once()
        call_kwargs = mock_basicConfig.call_args[1]
        assert call_kwargs['level'] == logging.INFO

    @patch('app.utils.logger_v2.setup_json_handler')
    @patch('app.utils.logger_v2.logging.basicConfig')
    def test_configure_logging_with_level(self, mock_basicConfig, mock_handler):
        """测试指定日志级别"""
        mock_handler.return_value = MagicMock()

        configure_logging(log_level="DEBUG")

        call_kwargs = mock_basicConfig.call_args[1]
        assert call_kwargs['level'] == logging.DEBUG

    @patch('app.utils.logger_v2.setup_json_handler')
    @patch('app.utils.logger_v2.logging.basicConfig')
    def test_configure_logging_with_file(self, mock_basicConfig, mock_handler):
        """测试指定日志文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            mock_handler.return_value = MagicMock()

            configure_logging(log_file=log_file)

            # 验证handler被调用
            mock_handler.assert_called_once_with(log_file)

    @patch('app.utils.logger_v2.setup_json_handler')
    @patch('app.utils.logger_v2.logging.basicConfig')
    def test_configure_logging_uppercase_level(self, mock_basicConfig, mock_handler):
        """测试大写日志级别"""
        mock_handler.return_value = MagicMock()

        configure_logging(log_level="WARNING")

        call_kwargs = mock_basicConfig.call_args[1]
        assert call_kwargs['level'] == logging.WARNING


class TestJsonFormatter:
    """测试JsonFormatter类"""

    @patch('app.utils.logger_v2.settings')
    def test_json_formatter_format(self, mock_settings):
        """测试JSON格式化"""
        mock_settings.environment = "test"

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            handler = setup_json_handler(log_file)
            formatter = handler.formatter

            # 创建一个日志记录
            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Test message",
                args=(),
                exc_info=None,
            )

            # 格式化日志
            result = formatter.format(record)

            # 验证是有效的JSON
            log_data = json.loads(result)
            assert log_data["level"] == "INFO"
            assert log_data["logger"] == "test.logger"
            assert log_data["message"] == "Test message"
            assert "timestamp" in log_data

    @patch('app.utils.logger_v2.settings')
    def test_json_formatter_with_extra_fields(self, mock_settings):
        """测试带额外字段的JSON格式化"""
        mock_settings.environment = "test"

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            handler = setup_json_handler(log_file)
            formatter = handler.formatter

            # 创建一个带额外字段的日志记录
            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Test message",
                args=(),
                exc_info=None,
            )
            record.user_id = "123"
            record.action = "login"

            result = formatter.format(record)

            log_data = json.loads(result)
            assert log_data["user_id"] == "123"
            assert log_data["action"] == "login"
