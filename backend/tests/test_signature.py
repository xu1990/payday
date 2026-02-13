"""
单元测试 - 签名验证模块 (app.core.signature)
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from app.core.signature import verify_signature, verify_timestamp
from app.core.exceptions import ValidationException


class TestVerifySignature:
    """测试签名验证函数"""

    @pytest.mark.asyncio
    async def test_verify_signature_valid_with_api_secret(self):
        """测试有效签名验证 - 配置了api_secret"""
        with patch('app.core.signature.settings') as mock_settings:
            mock_settings.api_secret = "test_secret_key"
            mock_settings.debug = False

            # 构建有效的签名
            url = "/api/v1/test"
            method = "POST"
            timestamp = "1234567890"
            nonce = "abc123"
            body = {"param1": "value1"}

            # 计算正确的签名
            import hashlib
            import hmac
            params = {"url": url, "method": method, "timestamp": timestamp, "nonce": nonce}
            params.update(body)
            sorted_items = sorted(params.items())
            sign_str = "&".join([f"{k}={v}" for k, v in sorted_items])
            expected_signature = hmac.new(
                mock_settings.api_secret.encode("utf-8"),
                sign_str.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            # 验证应该成功
            result = verify_signature(url, method, timestamp, nonce, expected_signature, body)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_signature_valid_without_body(self):
        """测试有效签名验证 - 没有请求体"""
        with patch('app.core.signature.settings') as mock_settings:
            mock_settings.api_secret = "test_secret_key"
            mock_settings.debug = False

            url = "/api/v1/test"
            method = "GET"
            timestamp = "1234567890"
            nonce = "abc123"

            # 计算正确的签名（没有body）
            import hashlib
            import hmac
            params = {"url": url, "method": method, "timestamp": timestamp, "nonce": nonce}
            sorted_items = sorted(params.items())
            sign_str = "&".join([f"{k}={v}" for k, v in sorted_items])
            expected_signature = hmac.new(
                mock_settings.api_secret.encode("utf-8"),
                sign_str.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            result = verify_signature(url, method, timestamp, nonce, expected_signature)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_signature_invalid(self):
        """测试无效签名验证"""
        with patch('app.core.signature.settings') as mock_settings:
            mock_settings.api_secret = "test_secret_key"
            mock_settings.debug = False

            with pytest.raises(ValidationException) as exc_info:
                verify_signature("/api/v1/test", "POST", "1234567890", "abc123", "invalid_signature")
            assert "Invalid request signature" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_signature_debug_mode_skip(self):
        """测试调试模式跳过签名验证"""
        with patch('app.core.signature.settings') as mock_settings:
            mock_settings.api_secret = None
            mock_settings.debug = True

            # 调试模式下没有api_secret应该返回True
            result = verify_signature("/api/v1/test", "POST", "1234567890", "abc123", "any_signature")
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_signature_no_api_secret_not_debug(self):
        """测试没有api_secret且非调试模式"""
        with patch('app.core.signature.settings') as mock_settings:
            mock_settings.api_secret = None
            mock_settings.debug = False

            with pytest.raises(ValidationException) as exc_info:
                verify_signature("/api/v1/test", "POST", "1234567890", "abc123", "any_signature")
            assert "API signature secret not configured" in str(exc_info.value)


class TestVerifyTimestamp:
    """测试时间戳验证函数"""

    def test_verify_timestamp_valid(self):
        """测试有效时间戳"""
        current_timestamp = str(int(time.time()))
        result = verify_timestamp(current_timestamp, max_age_seconds=60)
        assert result is True

    def test_verify_timestamp_old(self):
        """测试过期时间戳"""
        old_timestamp = str(int(time.time()) - 120)  # 2分钟前
        with pytest.raises(ValidationException) as exc_info:
            verify_timestamp(old_timestamp, max_age_seconds=60)
        assert "Request timestamp expired" in str(exc_info.value)

    def test_verify_timestamp_future(self):
        """测试未来时间戳"""
        future_timestamp = str(int(time.time()) + 120)  # 2分钟后
        with pytest.raises(ValidationException) as exc_info:
            verify_timestamp(future_timestamp, max_age_seconds=60)
        assert "Request timestamp expired" in str(exc_info.value)

    def test_verify_timestamp_invalid_format(self):
        """测试无效时间戳格式"""
        with pytest.raises(ValidationException) as exc_info:
            verify_timestamp("not_a_number")
        assert "Invalid timestamp format" in str(exc_info.value)

    def test_verify_timestamp_custom_max_age(self):
        """测试自定义最大有效期"""
        # 30秒前的时间戳，最大有效期60秒应该通过
        timestamp_30s_ago = str(int(time.time()) - 30)
        result = verify_timestamp(timestamp_30s_ago, max_age_seconds=60)
        assert result is True

        # 30秒前的时间戳，最大有效期20秒应该失败
        with pytest.raises(ValidationException):
            verify_timestamp(timestamp_30s_ago, max_age_seconds=20)

    def test_verify_timestamp_exactly_at_boundary(self):
        """测试边界情况 - 刚好在有效期边界"""
        current_timestamp = str(int(time.time()))
        # 刚好在边界内
        result = verify_timestamp(current_timestamp, max_age_seconds=60)
        assert result is True
