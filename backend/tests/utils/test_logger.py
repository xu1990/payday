"""测试日志工具"""
import pytest
import logging
from unittest.mock import patch

from app.utils.logger import get_logger


class TestGetLogger:
    """测试获取logger"""

    def test_returns_logger_instance(self):
        """测试返回logger实例"""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_logger_has_correct_name(self):
        """测试logger名称正确"""
        logger_name = "test.module.name"
        logger = get_logger(logger_name)
        assert logger.name == logger_name

    def test_logger_has_handlers(self):
        """测试logger有handlers"""
        logger = get_logger("test_with_handlers")
        assert len(logger.handlers) > 0

    def test_logger_same_instance_cached(self):
        """测试相同名称返回同一实例（缓存）"""
        logger1 = get_logger("cached_test")
        logger2 = get_logger("cached_test")
        # 由于handlers检查，第二次调用应返回同一实例
        assert logger1 is logger2

    def test_debug_mode_sets_debug_level(self):
        """测试debug模式设置DEBUG级别"""
        import app.utils.logger as logger_module
        original_settings = logger_module.settings

        try:
            # Mock settings with debug=True
            logger_module.settings.debug = True

            # 需要清除已存在的logger缓存
            logging.Logger.manager.loggerDict.pop('test_debug', None)

            logger = get_logger("test_debug")
            assert logger.level == logging.DEBUG
        finally:
            # Restore original settings
            logger_module.settings = original_settings

    def test_production_mode_sets_info_level(self):
        """测试生产模式设置INFO级别"""
        import app.utils.logger as logger_module
        original_settings = logger_module.settings

        try:
            # Mock settings with debug=False
            logger_module.settings.debug = False

            # 清除logger缓存
            logging.Logger.manager.loggerDict.pop('test_production', None)

            logger = get_logger("test_production")
            assert logger.level == logging.INFO
        finally:
            # Restore original settings
            logger_module.settings = original_settings

    def test_logger_can_log_messages(self, caplog):
        """测试logger可以记录日志"""
        logger = get_logger("test_logging")

        with caplog.at_level(logging.INFO):
            logger.info("Test info message")
            logger.warning("Test warning message")

        assert "Test info message" in caplog.text
        assert "Test warning message" in caplog.text

    def test_logger_format_includes_level(self, caplog):
        """测试日志格式包含级别"""
        logger = get_logger("test_format_level")

        with caplog.at_level(logging.INFO):
            logger.info("Test format")

        assert "INFO" in caplog.text
        assert "Test format" in caplog.text


class Mock:
    """简单的Mock类用于测试"""
    pass
