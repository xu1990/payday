"""
单元测试 - 自定义异常 (app.core.exceptions)
"""
import pytest
from fastapi import status

from app.core.exceptions import (
    PayDayException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ValidationException,
    RateLimitException,
    ExternalServiceException,
    BusinessException,
    error_response,
)


class TestAuthorizationException:
    """测试授权异常"""

    def test_authorization_exception_default(self):
        """测试默认授权异常"""
        exc = AuthorizationException()

        assert exc.message == "无权限访问"
        assert exc.code == "FORBIDDEN"
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.details is None

    def test_authorization_exception_custom_message(self):
        """测试自定义消息"""
        exc = AuthorizationException(message="自定义权限错误")

        assert exc.message == "自定义权限错误"
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_authorization_exception_with_details(self):
        """测试带详情的授权异常"""
        details = {"resource": "admin", "action": "delete"}
        exc = AuthorizationException(details=details)

        assert exc.details == details


class TestExternalServiceException:
    """测试外部服务异常"""

    def test_external_service_exception_default(self):
        """测试默认外部服务异常"""
        exc = ExternalServiceException()

        assert exc.message == "外部服务调用失败"
        assert "EXTERNAL_SERVICE_" in exc.code
        assert exc.code.endswith("_ERROR")
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_external_service_exception_with_service(self):
        """测试指定服务名称"""
        exc = ExternalServiceException(service="wechat")

        assert exc.code == "EXTERNAL_SERVICE_WECHAT_ERROR"

    def test_external_service_exception_custom_message(self):
        """测试自定义消息"""
        exc = ExternalServiceException(
            message="微信支付失败",
            service="payment",
        )

        assert exc.message == "微信支付失败"
        assert exc.code == "EXTERNAL_SERVICE_PAYMENT_ERROR"

    def test_external_service_exception_with_details(self):
        """测试带详情的外部服务异常"""
        details = {"error_code": "PAY_ERROR", "transaction_id": "12345"}
        exc = ExternalServiceException(
            service="payment",
            details=details,
        )

        assert exc.details == details


class TestPayDayExceptionBase:
    """测试基础异常类"""

    def test_payday_exception_minimal(self):
        """测试最小参数"""
        exc = PayDayException(message="错误")

        assert exc.message == "错误"
        assert exc.code == "INTERNAL_ERROR"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details is None

    def test_payday_exception_custom(self):
        """测试自定义值"""
        exc = PayDayException(
            message="自定义错误",
            code="CUSTOM_ERROR",
            status_code=418,
            details={"field": "value"},
        )

        assert exc.message == "自定义错误"
        assert exc.code == "CUSTOM_ERROR"
        assert exc.status_code == 418
        assert exc.details == {"field": "value"}


class TestOtherExceptions:
    """测试其他异常类的初始化"""

    def test_authentication_exception(self):
        """测试认证异常"""
        exc = AuthenticationException()

        assert exc.message == "认证失败"
        assert exc.code == "AUTH_FAILED"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_not_found_exception(self):
        """测试资源不存在异常"""
        exc = NotFoundException("资源不存在")

        assert exc.message == "资源不存在"
        assert exc.code == "NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_validation_exception(self):
        """测试验证异常"""
        details = {"email": "格式错误"}
        exc = ValidationException("验证失败", details=details)

        assert exc.message == "验证失败"
        assert exc.code == "VALIDATION_ERROR"
        assert exc.details == details

    def test_rate_limit_exception(self):
        """测试限流异常"""
        exc = RateLimitException("请求过于频繁", details={"retry_after": 60})

        assert exc.message == "请求过于频繁"
        assert exc.code == "RATE_LIMIT"
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_business_exception(self):
        """测试业务异常"""
        exc = BusinessException("业务逻辑错误")

        assert exc.message == "业务逻辑错误"
        assert exc.code == "BUSINESS_ERROR"


class TestErrorResponse:
    """测试 error_response 辅助函数"""

    def test_error_response_basic(self):
        """测试基本错误响应"""
        response = error_response(
            status_code=400,
            message="错误的请求",
        )

        assert response.status_code == 400

    def test_error_response_with_code(self):
        """测试带 code 的错误响应"""
        response = error_response(
            status_code=404,
            message="未找到",
            code="NOT_FOUND",
        )

        assert response.status_code == 404

    def test_error_response_with_all_params(self):
        """测试完整参数的错误响应"""
        response = error_response(
            status_code=422,
            message="验证失败",
            code="VALIDATION_ERROR",
            details={"field": "email"},
        )

        assert response.status_code == 422
