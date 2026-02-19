"""
全局异常处理中间件
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .exceptions import (
    PayDayException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ValidationException,
    RateLimitException,
    ExternalServiceException,
    error_response,
    success_response,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def payday_exception_handler(
    request: Request, exc: PayDayException
) -> JSONResponse:
    """处理 PayDay 自定义异常"""
    # 记录错误日志
    logger.warning(
        f"Business exception: {exc.code} - {exc.message}",
        extra={
            "code": exc.code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )

    return error_response(
        status_code=exc.status_code,
        message=exc.message,
        code=exc.code,
        details=exc.details,
    )


async def http_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """处理 FastAPI HTTPException"""
    logger.warning(
        f"HTTP exception: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return error_response(
        status_code=getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR),
        message=str(exc.detail) if hasattr(exc, "detail") else str(exc),
        code="HTTP_ERROR",
    )


async def validation_exception_handler(
    request: Request, exc: ValidationException
) -> JSONResponse:
    """处理参数验证异常"""
    logger.info(
        f"Validation error: {exc.message}",
        extra={
            "path": request.url.path,
            "details": exc.details,
        },
    )

    return error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=exc.message,
        code=exc.code,
        details=exc.details,
    )


async def auth_exception_handler(
    request: Request, exc: AuthenticationException
) -> JSONResponse:
    """处理认证异常"""
    logger.warning(
        f"Authentication failed: {request.url.path}",
        extra={"code": exc.code},
    )

    return error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message=exc.message,
        code=exc.code,
    )


async def database_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """处理数据库异常"""
    logger.error(
        f"Database error: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="数据库错误，请稍后重试",
        code="DATABASE_ERROR",
    )


async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """处理所有未捕获的异常"""
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    # 生产环境不暴露详细错误信息
    from app.core.config import get_settings

    settings = get_settings()
    if settings.debug:
        message = f"{type(exc).__name__}: {str(exc)}"
    else:
        message = "服务器内部错误，请稍后重试"

    return error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=message,
        code="INTERNAL_ERROR",
    )


def setup_exception_handlers(app):
    """设置全局异常处理器"""

    # 自定义业务异常
    app.add_exception_handler(PayDayException, payday_exception_handler)

    # 认证异常
    app.add_exception_handler(AuthenticationException, auth_exception_handler)

    # 参数验证异常
    app.add_exception_handler(ValidationException, validation_exception_handler)

    # 数据库异常
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)

    # 通用异常处理
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered")
