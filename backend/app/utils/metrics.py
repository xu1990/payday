"""
Prometheus 监控指标 - 技术方案 6.1.1
提供 HTTP 请求、数据库、缓存等关键指标暴露
"""
import time
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from functools import wraps
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_logger

logger = get_logger(__name__)

# 使用自定义 registry，避免与其他服务冲突
registry = CollectorRegistry()

# ============== HTTP 请求指标 ==============

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    registry=registry
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint'],
    registry=registry
)

# ============== 业务指标 ==============

# 用户相关
users_total = Gauge(
    'users_total',
    'Total number of users',
    registry=registry
)

users_active = Gauge(
    'users_active_total',
    'Number of active users (last 24h)',
    registry=registry
)

# 帖子相关
posts_total = Gauge(
    'posts_total',
    'Total number of posts',
    ['status'],  # normal, hidden, deleted
    registry=registry
)

posts_created_total = Counter(
    'posts_created_total',
    'Total posts created',
    registry=registry
)

# 评论相关
comments_total = Gauge(
    'comments_total',
    'Total number of comments',
    registry=registry
)

comments_created_total = Counter(
    'comments_created_total',
    'Total comments created',
    registry=registry
)

# 点赞相关
likes_total = Gauge(
    'likes_total',
    'Total number of likes',
    ['target_type'],  # post, comment
    registry=registry
)

# ============== 数据库连接池 ==============

db_pool_size = Gauge(
    'db_pool_size',
    'Database connection pool size',
    registry=registry
)

db_pool_overflow = Gauge(
    'db_pool_overflow',
    'Database connection pool overflow',
    registry=registry
)

db_pool_checked_out = Gauge(
    'db_pool_checked_out',
    'Database connections currently checked out',
    registry=registry
)

# ============== 缓存指标 ==============

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],  # user, post, payday, etc.
    registry=registry
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry
)

cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['cache_type', 'operation'],  # operation: get, set, delete
    registry=registry
)

# ============== 风控指标 ==============

risk_checks_total = Counter(
    'risk_checks_total',
    'Total risk checks performed',
    ['target_type', 'result'],  # target_type: post, comment; result: approve, reject, manual
    registry=registry
)

risk_check_duration_seconds = Histogram(
    'risk_check_duration_seconds',
    'Risk check duration in seconds',
    ['check_type'],  # text, image, ocr
    registry=registry
)

# ============== 任务队列指标 ==============

celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks executed',
    ['task_name', 'status'],  # status: success, failure, retry
    registry=registry
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    registry=registry
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in Celery queue',
    ['queue_name'],
    registry=registry
)

# ============== 应用信息 ==============

app_info = Info(
    'app',
    'Application information',
    registry=registry
)


def track_request_time(func: Callable):
    """
    装饰器：跟踪函数执行时间

    用法:
        @track_request_time
        async def my_function():
            ...
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            # 使用函数名作为 endpoint
            endpoint = func.__name__
            http_request_duration_seconds.labels(
                method='async',
                endpoint=endpoint
            ).observe(duration)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            endpoint = func.__name__
            http_request_duration_seconds.labels(
                method='sync',
                endpoint=endpoint
            ).observe(duration)

    # 根据是否是协程函数选择包装器
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Prometheus 中间件 - 自动记录 HTTP 请求指标

    技术方案 6.1.1 - 暴露监控指标端点
    """

    async def dispatch(self, request: Request, call_next):
        # 跳过 /metrics 端点本身
        if request.url.path == '/metrics':
            return await call_next(request)

        # 提取路径（去除查询参数）
        path = request.url.path

        # 跳过健康检查等端点
        if path in ['/health', '/readiness', '/liveness']:
            return await call_next(request)

        # 记录请求开始
        http_requests_in_progress.labels(
            method=request.method,
            endpoint=path
        ).inc()
        start_time = time.time()

        try:
            # 执行请求
            response: Response = await call_next(request)

            # 记录请求完成
            status = response.status_code
            duration = time.time() - start_time

            # 更新指标
            http_requests_total.labels(
                method=request.method,
                endpoint=path,
                status=status
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=path
            ).observe(duration)

            return response

        finally:
            # 减少进行中的请求数
            http_requests_in_progress.labels(
                method=request.method,
                endpoint=path
            ).dec()


async def get_db_pool_metrics():
    """获取数据库连接池指标"""
    try:
        from app.core.database import _get_async_engine
        from sqlalchemy.pool import NullPool
        engine = _get_async_engine()

        pool = engine.pool

        # SQLite 使用 NullPool，没有连接池概念，跳过收集
        if isinstance(pool, NullPool):
            return

        db_pool_size.set(pool.size())
        db_pool_overflow.set(pool.overflow())
        db_pool_checked_out.set(pool.checkedout())

    except Exception as e:
        logger.warning(f"Failed to collect DB pool metrics: {e}")


async def collect_application_metrics():
    """
    收集应用级别指标

    可以在定时任务中定期调用
    """
    try:
        # 收集数据库连接池指标
        await get_db_pool_metrics()

        # 这里可以添加其他应用级指标收集
        # 例如: 用户统计、帖子统计等

    except Exception as e:
        logger.warning(f"Failed to collect application metrics: {e}")


def get_metrics_text() -> bytes:
    """
    获取 Prometheus 文本格式的指标

    用于 /metrics 端点返回
    """
    return generate_latest(registry)


def get_metrics_content_type() -> str:
    """获取 metrics 内容类型"""
    return CONTENT_TYPE_LATEST


# ============== 辅助函数 ==============

def inc_cache_hits(cache_type: str):
    """增加缓存命中计数"""
    cache_hits_total.labels(cache_type=cache_type).inc()


def inc_cache_misses(cache_type: str):
    """增加缓存未命中计数"""
    cache_misses_total.labels(cache_type=cache_type).inc()


def inc_cache_operations(cache_type: str, operation: str):
    """增加缓存操作计数"""
    cache_operations_total.labels(cache_type=cache_type, operation=operation).inc()


def inc_posts_created():
    """增加创建帖子计数"""
    posts_created_total.inc()


def inc_comments_created():
    """增加创建评论计数"""
    comments_created_total.inc()


def inc_risk_checks(target_type: str, result: str):
    """增加风控检查计数"""
    risk_checks_total.labels(target_type=target_type, result=result).inc()


def observe_risk_check_duration(check_type: str, duration: float):
    """记录风控检查耗时"""
    risk_check_duration_seconds.labels(check_type=check_type).observe(duration)


def set_app_info(version: str, build_time: str, git_commit: Optional[str] = None):
    """设置应用信息"""
    info = {
        'version': version,
        'build_time': build_time,
    }
    if git_commit:
        info['git_commit'] = git_commit
    app_info.info(info)
