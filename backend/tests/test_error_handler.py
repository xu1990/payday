"""
单元测试 - 全局异常处理 (app.core.error_handler)
"""
import pytest
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.error_handler import (
    payday_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    auth_exception_handler,
    database_exception_handler,
    general_exception_handler,
    setup_exception_handlers,
)
from app.core.exceptions import (
    PayDayException,
    AuthenticationException,
    NotFoundException,
    ValidationException,
    RateLimitException,
    ExternalServiceException,
    error_response,
)


class TestPaydayExceptionHandler:
    """测试 PayDay 异常处理器"""

    @pytest.mark.asyncio
    async def test_payday_exception_handler(self):
        """测试自定义异常处理"""
        exc = PayDayException(
            message="测试错误",
            code="TEST_ERROR",
            status_code=400,
            details={"field": "value"},
        )

        # 创建 mock request
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test/path"
        request.method = "GET"

        response = await payday_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_payday_exception_without_details(self):
        """测试没有详情的异常"""
        exc = PayDayException(
            message="简单错误",
            code="SIMPLE_ERROR",
        )

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "POST"

        response = await payday_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)

    @pytest.mark.asyncio
    async def test_not_found_exception_handler(self):
        """测试 NotFoundException 处理"""
        exc = NotFoundException("资源不存在")

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/resource/123"
        request.method = "GET"

        response = await payday_exception_handler(request, exc)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """测试 ValidationException 通过 payday 处理"""
        exc = ValidationException("参数错误", details={"field": "email"})

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.method = "POST"

        response = await payday_exception_handler(request, exc)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rate_limit_exception_handler(self):
        """测试 RateLimitException 处理"""
        exc = RateLimitException("请求过于频繁", details={"retry_after": 60})

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"

        response = await payday_exception_handler(request, exc)

        assert response.status_code == 429


class TestHTTPExceptionHandler:
    """测试 HTTPException 处理器"""

    @pytest.mark.asyncio
    async def test_http_exception_handler_with_detail(self):
        """测试带详情的 HTTPException"""
        exc = HTTPException(status_code=400, detail="错误的请求")

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.method = "POST"

        response = await http_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_http_exception_handler_without_detail(self):
        """测试不带详情的 HTTPException"""
        exc = Exception("普通错误")

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"

        response = await http_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


class TestValidationExceptionHandler:
    """测试参数验证异常处理器"""

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """测试 ValidationException 处理"""
        exc = ValidationException(
            "验证失败",
            details={"email": "格式错误"},
        )

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/user"
        request.method = "POST"

        response = await validation_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validation_exception_without_details(self):
        """测试没有详情的验证异常"""
        exc = ValidationException("验证失败")

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.method = "PUT"

        response = await validation_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)


class TestAuthExceptionHandler:
    """测试认证异常处理器"""

    @pytest.mark.asyncio
    async def test_auth_exception_handler(self):
        """测试 AuthenticationException 处理"""
        exc = AuthenticationException("未授权访问")

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/admin"
        request.method = "GET"

        response = await auth_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 401


class TestDatabaseExceptionHandler:
    """测试数据库异常处理器"""

    @pytest.mark.asyncio
    async def test_database_exception_handler(self):
        """测试 SQLAlchemyError 处理"""
        exc = SQLAlchemyError("数据库连接失败")

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/data"
        request.method = "GET"

        response = await database_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_database_integrity_error(self):
        """测试数据库完整性错误"""
        from sqlalchemy.exc import IntegrityError
        exc = IntegrityError("UNIQUE constraint failed", {}, None)

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/create"
        request.method = "POST"

        response = await database_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


class TestGeneralExceptionHandler:
    """测试通用异常处理器"""

    @pytest.mark.asyncio
    async def test_general_exception_debug_mode(self):
        """测试调试模式下的异常处理"""
        exc = ValueError("某个值错误")

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"

        # Mock debug mode
        from unittest.mock import patch
        with patch('app.core.config.get_settings') as mock_settings:
            mock_settings.return_value.debug = True
            response = await general_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_general_exception_production_mode(self):
        """测试生产模式下的异常处理"""
        exc = RuntimeError("运行时错误")

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.method = "POST"

        # Mock production mode
        from unittest.mock import patch
        with patch('app.core.config.get_settings') as mock_settings:
            mock_settings.return_value.debug = False
            response = await general_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_general_exception_custom_exception(self):
        """测试自定义异常的通用处理"""
        class CustomError(Exception):
            pass

        exc = CustomError("自定义错误")

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/custom"
        request.method = "DELETE"

        from unittest.mock import patch
        with patch('app.core.config.get_settings') as mock_settings:
            mock_settings.return_value.debug = True
            response = await general_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)


class TestSetupExceptionHandlers:
    """测试设置异常处理器"""

    def test_setup_exception_handlers(self):
        """测试注册所有异常处理器"""
        from fastapi import FastAPI

        app = FastAPI()

        setup_exception_handlers(app)

        # 验证异常处理器已注册（通过检查不会报错）
        assert app is not None

    def test_setup_registers_all_handlers(self):
        """测试所有预期的处理器都已注册"""
        from fastapi import FastAPI

        app = FastAPI()

        # 获取注册前的异常处理器数量
        before_count = len(app.exception_handlers)

        setup_exception_handlers(app)

        # 注册后应该有更多的异常处理器
        after_count = len(app.exception_handlers)
        assert after_count > before_count


class TestErrorResponseHelper:
    """测试 error_response 辅助函数"""

    def test_error_response_basic(self):
        """测试基本错误响应"""
        response = error_response(
            status_code=400,
            message="错误的请求",
            code="BAD_REQUEST",
        )

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    def test_error_response_with_details(self):
        """测试带详情的错误响应"""
        response = error_response(
            status_code=422,
            message="验证失败",
            code="VALIDATION_ERROR",
            details={"field": "email", "error": "invalid"},
        )

        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

    def test_error_response_without_code(self):
        """测试不带 code 的错误响应"""
        response = error_response(
            status_code=500,
            message="服务器错误",
        )

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


# Mock class for testing
class MagicMock:
    """简单的 Mock 类"""
    def __init__(self, spec=None):
        self.spec = spec

    def __getattr__(self, name):
        if name == "url":
            return self
        return MagicMock()

    def __call__(self, *args, **kwargs):
        return MagicMock()
