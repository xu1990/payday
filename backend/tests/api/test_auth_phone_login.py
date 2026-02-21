"""
测试手机号登录相关的 schema 验证

测试 LoginRequest 和 LoginResponse 支持 phoneNumberCode 参数
"""
import pytest
from app.schemas.auth import LoginRequest, LoginResponse


class TestLoginRequestWithPhoneCode:
    """测试 LoginRequest schema 支持 phoneNumberCode"""

    def test_login_request_with_phone_code(self):
        """Test LoginRequest accepts phoneNumberCode"""
        data = {
            "code": "test_wechat_code",
            "phoneNumberCode": "test_phone_code"
        }
        request = LoginRequest(**data)
        assert request.code == "test_wechat_code"
        assert request.phoneNumberCode == "test_phone_code"

    def test_login_request_without_phone_code(self):
        """Test LoginRequest works without phoneNumberCode (backward compat)"""
        data = {"code": "test_wechat_code"}
        request = LoginRequest(**data)
        assert request.code == "test_wechat_code"
        assert request.phoneNumberCode is None


class TestLoginResponseWithPhone:
    """测试 LoginResponse schema 包含手机号信息"""

    def test_login_response_with_phone(self):
        """Test LoginResponse includes phone fields"""
        user_data = {
            "id": "test_id",
            "anonymous_name": "测试用户",
            "avatar": "https://example.com/avatar.jpg",
            "phoneNumber": "138****8888",  # Masked
            "phoneVerified": True
        }
        response_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "user": user_data
        }
        response = LoginResponse(**response_data)
        assert response.user["phoneNumber"] == "138****8888"
        assert response.user["phoneVerified"] is True

    def test_login_response_without_phone(self):
        """Test LoginResponse works without phone fields (backward compat)"""
        user_data = {
            "id": "test_id",
            "anonymous_name": "测试用户",
            "avatar": "https://example.com/avatar.jpg"
        }
        response_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "user": user_data
        }
        response = LoginResponse(**response_data)
        assert response.user["id"] == "test_id"
        assert response.user["anonymous_name"] == "测试用户"
