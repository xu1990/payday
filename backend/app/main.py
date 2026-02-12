"""
薪日 PayDay 主服务入口 - 技术方案 2.1.1 + 6.1 监控
集成 Prometheus 监控指标 + Sentry 错误追踪
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting PayDay backend...")

    # 初始化 Sentry
    init_on_startup()

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


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS 中间件
# SECURITY: 使用环境变量配置白名单，允许跨域认证请求
_cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus 监控中间件
# 技术方案 6.1.1 - HTTP 请求指标收集
app.add_middleware(PrometheusMiddleware)


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
