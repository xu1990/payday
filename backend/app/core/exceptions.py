"""
统一异常处理 - 技术方案 安全方案
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class PayDayException(Exception):
    """基础异常类"""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class BusinessException(PayDayException):
    """业务逻辑异常"""

    def __init__(
        self,
        message: str,
        code: str = "BUSINESS_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST, details)


class AuthenticationException(PayDayException):
    """认证异常"""

    def __init__(
        self,
        message: str = "认证失败",
        code: str = "AUTH_FAILED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_401_UNAUTHORIZED, details)


class AuthorizationException(PayDayException):
    """授权异常"""

    def __init__(
        self,
        message: str = "无权限访问",
        code: str = "FORBIDDEN",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_403_FORBIDDEN, details)


class NotFoundException(PayDayException):
    """资源不存在异常"""

    def __init__(
        self,
        message: str = "资源不存在",
        code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_404_NOT_FOUND, details)


class ValidationException(PayDayException):
    """参数验证异常"""

    def __init__(
        self,
        message: str = "参数验证失败",
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class RateLimitException(PayDayException):
    """限流异常"""

    def __init__(
        self,
        message: str = "请求过于频繁",
        code: str = "RATE_LIMIT",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_429_TOO_MANY_REQUESTS, details)


class ExternalServiceException(PayDayException):
    """外部服务异常"""

    def __init__(
        self,
        message: str = "外部服务调用失败",
        service: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
    ):
        code = f"EXTERNAL_SERVICE_{service.upper()}_ERROR"
        super().__init__(message, code, status.HTTP_503_SERVICE_UNAVAILABLE, details)


def error_response(
    status_code: int,
    message: str,
    code: str = "ERROR",
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """统一错误响应格式"""
    content: Dict[str, Any] = {
        "code": code,
        "message": message,
        "details": details or {},
    }
    return JSONResponse(status_code=status_code, content=content)


def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: str = "SUCCESS",
) -> JSONResponse:
    """统一成功响应格式"""
    content: Dict[str, Any] = {
        "code": code,
        "message": message,
        "details": data if data is not None else {},
    }
    return JSONResponse(content=content)
