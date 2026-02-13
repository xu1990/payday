"""
单元测试 - 微信小程序工具 (app.utils.wechat)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.utils.wechat import code2session


class TestCode2Session:
    """测试 code2session 函数"""

    @pytest.mark.asyncio
    async def test_code2session_success(self):
        """测试成功换取openid"""
        mock_response = {
            "openid": "test_openid_123",
            "session_key": "test_session_key",
            "unionid": "test_unionid",
        }

        with patch('app.utils.wechat.get_settings') as mock_settings:
            mock_settings.wechat_app_id = "test_app_id"
            mock_settings.wechat_app_secret = "test_secret"

            with patch('app.utils.wechat.httpx.AsyncClient') as mock_client:
                mock_resp = MagicMock()
                mock_resp.json.return_value = mock_response

                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

                result = await code2session("test_code")

                assert result["openid"] == "test_openid_123"
                assert result["session_key"] == "test_session_key"

    @pytest.mark.asyncio
    async def test_code2session_invalid_code(self):
        """测试无效code"""
        mock_response = {
            "errcode": 40029,
            "errmsg": "invalid code",
        }

        with patch('app.utils.wechat.get_settings') as mock_settings:
            mock_settings.wechat_app_id = "test_app_id"
            mock_settings.wechat_app_secret = "test_secret"

            with patch('app.utils.wechat.httpx.AsyncClient') as mock_client:
                mock_resp = MagicMock()
                mock_resp.json.return_value = mock_response

                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

                result = await code2session("invalid_code")

                assert result["errcode"] == 40029
                assert "invalid code" in result["errmsg"]

    @pytest.mark.asyncio
    async def test_code2session_http_error(self):
        """测试HTTP请求错误"""
        with patch('app.utils.wechat.get_settings') as mock_settings:
            mock_settings.wechat_app_id = "test_app_id"
            mock_settings.wechat_app_secret = "test_secret"

            with patch('app.utils.wechat.httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("HTTP error")

                with pytest.raises(Exception):
                    await code2session("test_code")
