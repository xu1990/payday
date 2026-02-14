"""
薪日 PayDay 主服务入口 - 技术方案 2.1.1 + 6.1 监控
集成 Prometheus 监控指标 + Sentry 错误追踪
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import async_session_maker
from app.core.error_handler import setup_exception_handlers
from app.api.v1 import api_router
from app.services.cache_preheat import preheat_all
from app.utils.logger import get_logger
from app.utils.metrics import (
    PrometheusMiddleware,
    get_metrics_text,
    get_metrics_content_type,
    set_app_info,
    collect_application_metrics,
)
from app.utils.sentry import init_on_startup
from app.utils import date as date_utils

logger = get_logger(__name__)
settings = get_settings()


# 请求大小限制配置
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting PayDay backend...")

    # 初始化 Sentry
    init_on_startup()

    # 初始化 Redis 连接
    from app.core.cache import get_redis_client
    try:
        await get_redis_client()
        logger.info("Redis connection initialized")
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}")

    # 设置应用信息
    import os
    git_commit = os.getenv('GIT_COMMIT', None)
    set_app_info(
        version=getattr(settings, 'app_version', '1.0.0'),
        build_time=date_utils.now().isoformat(),
        git_commit=git_commit,
    )

    # 预热缓存
    try:
        async with async_session_maker() as db:
            results = await preheat_all(db)
            total = sum(results.values())
            logger.info(f"Cache preheated: {total} items")
    except Exception as e:
        logger.warning(f"Cache preheating failed: {e}")

    # 启动指标收集定时任务
    import asyncio

    async def metrics_collector():
        """定期收集应用指标"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟收集一次
                await collect_application_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Metrics collection failed: {e}")

    # 启动指标收集任务
    metrics_task = asyncio.create_task(metrics_collector())

    yield

    # 取消指标收集任务
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass

    # 关闭时执行
    logger.info("Shutting down PayDay backend...")

    # 关闭 Redis 连接
    from app.core.cache import close_redis
    try:
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Redis close failed: {e}")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)


def custom_openapi():
    """
    自定义 OpenAPI 架构信息
    增强Swagger 文档的元数据和说明
    """
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title="薪日 PayDay API",
        version=getattr(settings, 'app_version', '1.0.0'),
        description="""
# 薪日 PayDay 小程序 API

## 概述

薪日是一个为工人设计的薪日心情追踪小程序，支持社交分享和社区互动。

## 主要功能

- **用户管理**: 微信小程序登录、用户信息管理
- **薪日配置**: 设置发薪日、获取薪日倒计时
- **薪资记录**: 加密记录每月薪资（HKDF + Fernet 加密）
- **社区功能**: 发帖、评论、点赞、关注
- **通知系统**: 推送通知和站内消息
- **会员系统**: 会员订阅和订单管理
- **数据统计**: 个人数据和统计分析

## 认证方式

### 小程序端（用户）

使用 **JWT Bearer Token** 认证：

```http
Authorization: Bearer <access_token>
```

- **Access Token**: 有效期 15 分钟
- **Refresh Token**: 有效期 7 天
- 获取方式: `/api/v1/auth/wechat`

### 管理后台

使用 **JWT Bearer Token** 认证（带 admin scope）：

```http
Authorization: Bearer <admin_token>
```

- **Token**: 包含 `scope: admin` 声明
- 获取方式: `/api/v1/admin/login`

## 数据加密

- **薪资金额**: 使用 HKDF 密钥派生 + Fernet 对称加密
- **每条记录**: 独立的 32 字节随机 salt
- **密钥管理**: 基于 `ENCRYPTION_SECRET_KEY` 环境变量

## 速率限制

- **普通端点**: 100 请求/分钟
- **登录端点**: 10 请求/分钟
- **上传端点**: 20 请求/分钟

## 错误响应

所有错误响应遵循统一格式：

```json
{
  "code": "ERROR_CODE",
  "message": "用户友好的错误消息",
  "details": {}  // 可选的详细信息
}
```

## 技术栈

- **框架**: FastAPI (Python 3.11+)
- **数据库**: MySQL 8.0+ (SQLAlchemy 异步 ORM)
- **缓存**: Redis (缓存回退到内存)
- **任务队列**: Celery + Redis
- **对象存储**: 腾讯云 COS / 阿里云 OSS
- **内容安全**: 腾讯云天御

## 文档

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Schema**: `/openapi.json`

---

**技术方案**: 参见 `docs/技术方案_v1.0.md`
**Sprint 规划**: 参见 `docs/迭代规划_Sprint与任务.md`
        """,
        routes=app.routes,
        tags=[
            {
                "name": "认证",
                "description": "用户和管理员认证相关接口"
            },
            {
                "name": "用户",
                "description": "用户信息管理"
            },
            {
                "name": "薪日",
                "description": "薪日配置和倒计时"
            },
            {
                "name": "薪资",
                "description": "薪资记录管理（加密存储）"
            },
            {
                "name": "社区",
                "description": "帖子、评论、点赞等社交功能"
            },
            {
                "name": "通知",
                "description": "推送通知和站内消息"
            },
            {
                "name": "会员",
                "description": "会员订阅和订单管理"
            },
            {
                "name": "管理后台",
                "description": "管理员专用接口"
            },
        ]
    )

    # 添加服务器信息（开发/生产环境）
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "开发环境"
        },
        {
            "url": "https://api.yourdomain.com",
            "description": "生产环境（请替换为实际域名）"
        }
    ]

    # 添加联系信息
    openapi_schema["info"]["contact"] = {
        "name": "PayDay Team",
        "email": "support@payday.com",
        "url": "https://github.com/yourorg/payday"
    }

    # 添加许可证信息
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# 覆盖默认的 OpenAPI 函数
app.openapi = custom_openapi

# CORS 中间件
# SECURITY: 使用环境变量配置白名单，限制跨域请求
_cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

# 记录 CORS 配置（调试模式）
if settings.debug:
    logger.info(f"CORS 允许的源: {_cors_origins}")
else:
    # 生产环境警告
    if "*" in _cors_origins:
        logger.warning("⚠️ 生产环境中 CORS 配置为通配符 '*'，这是不安全的！")
    if any("localhost" in origin or "127.0.0.1" in origin for origin in _cors_origins):
        logger.warning("⚠️ 生产环境中 CORS 配置包含 localhost，建议移除")

# 明确允许的 HTTP 方法（不使用通配符）
_allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

# 明确允许的请求头（不使用通配符）
_allowed_headers = [
    "Content-Type",
    "Authorization",
    "X-Timestamp",  # 签名相关（可选）
    "X-Nonce",      # 签名相关（可选）
    "X-Signature",  # 签名相关（可选）
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=_allowed_methods,
    allow_headers=_allowed_headers,
)

# Prometheus 监控中间件
# 技术方案 6.1.1 - HTTP 请求指标收集
app.add_middleware(PrometheusMiddleware)


# 请求大小限制中间件
# SECURITY: 防止 DoS 攻击 - 限制请求体大小
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """检查请求大小，防止 DoS 攻击"""
    # 检查 Content-Length 头
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            length = int(content_length)
            if length > MAX_REQUEST_SIZE:
                logger.warning(
                    f"Request too large: {length} bytes from {request.client.host if request.client else 'unknown'}"
                )
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request body too large. Maximum size is {MAX_REQUEST_SIZE // (1024*1024)}MB"}
                )
        except ValueError:
            pass  # Invalid content-length, let the request proceed

    # 对于没有 Content-Length 的请求，无法提前检查
    # 但 Starlette 会在解析时自动限制
    return await call_next(request)


@app.get("/health")
def health():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """
    Prometheus 指标端点

    技术方案 6.1.1 - 暴露监控指标
    """
    metrics_data = get_metrics_text()
    return Response(
        content=metrics_data,
        media_type=get_metrics_content_type(),
    )


app.include_router(api_router)

# 设置全局异常处理器
setup_exception_handlers(app)


@app.get("/")
def root():
    return {"app": settings.app_name}
