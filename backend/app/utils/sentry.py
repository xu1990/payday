"""
Sentry 错误追踪集成 - 技术方案 6.2
生产环境错误收集与性能监控
"""
import os
from typing import Optional
from sentry_sdk import init as sentry_init, capture_exception, capture_message, set_tag
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Sentry 初始化状态
_sentry_initialized = False


def init_sentry():
    """
    初始化 Sentry

    技术方案 6.2 - 生产环境错误追踪
    """
    global _sentry_initialized

    settings = get_settings()

    # 检查是否配置了 Sentry DSN
    sentry_dsn = os.getenv('SENTRY_DSN')
    if not sentry_dsn:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return

    if _sentry_initialized:
        return

    try:
        # 从环境变量读取配置
        environment = os.getenv('ENVIRONMENT', 'development')
        release = os.getenv('GIT_COMMIT', 'unknown')

        sentry_init(
            dsn=sentry_dsn,
            # 环境信息
            environment=environment,
            release=release,

            # 采样率（生产环境可适当降低）
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.0')),

            # 集成
            integrals=[
                FastApiIntegration(),
                CeleryIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],

            # 过滤敏感信息
            before_send=before_send_filter,

            # 忽略的异常类型
            ignore_errors=[
                # 404 等客户端错误可以不上报
                # 'fastapi.exceptions.HTTPException',
            ],

            # 服务器名称
            server_name=os.getenv('SERVER_NAME', 'payday-backend'),
        )

        _sentry_initialized = True
        logger.info(f"Sentry initialized: environment={environment}, release={release}")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_filter(event, hint):
    """
    发送前过滤敏感信息

    技术方案 6.2 - 数据脱敏
    """
    if event is None:
        return None

    # 过滤请求头中的敏感信息
    request = event.get('request', {})
    headers = request.get('headers', {})

    sensitive_headers = ['authorization', 'cookie', 'x-api-key']
    filtered_headers = {k: v for k, v in headers.items()
                     if k.lower() not in sensitive_headers}

    if filtered_headers != headers:
        event['request']['headers'] = filtered_headers

    # 过滤查询参数中的敏感信息
    query_string = request.get('query_string', '')
    if query_string:
        # TODO: 更精确的敏感参数过滤
        event['request']['query_string'] = '[FILTERED]'

    # 过滤 body 中的敏感字段
    body = request.get('data', {})
    if body and isinstance(body, dict):
        sensitive_fields = ['password', 'token', 'secret', 'key']
        for field in sensitive_fields:
            if field in body:
                body[field] = '[FILTERED]'

    return event


def capture_exception exc: Exception, level: str = 'error', tags: Optional[dict] = None, extra: Optional[dict] = None):
    """
    捕获并上报异常到 Sentry

    Args:
        exc: 异常对象
        level: 日志级别 (error, warning, info)
        tags: 额外标签
        extra: 额外数据
    """
    if not _sentry_initialized:
        logger.warning(f"Sentry not initialized, exception not sent: {exc}")
        # 仅记录日志
        logger.error(f"Exception: {exc}", exc_info=exc)
        return

    # 添加标签
    if tags:
        for key, value in tags.items():
            set_tag(key, value)

    # 上报到 Sentry
    with configure_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        capture_exception(exc)

    # 同时记录到本地日志
    logger.error(f"Exception captured by Sentry: {exc}", exc_info=exc)


def capture_message message: str, level: str = 'info', tags: Optional[dict] = None):
    """
    捕获并上报消息到 Sentry

    Args:
        message: 消息内容
        level: 日志级别
        tags: 额外标签
    """
    if not _sentry_initialized:
        logger.debug(f"Sentry not initialized, message not sent: {message}")
        return

    # 添加标签
    if tags:
        for key, value in tags.items():
            set_tag(key, value)

    # 上报到 Sentry
    from sentry_sdk import capture_message as sentry_capture_message
    sentry_capture_message(message, level=level)

    # 同时记录到本地日志
    if level == 'error':
        logger.error(f"Message captured by Sentry: {message}")
    elif level == 'warning':
        logger.warning(f"Message captured by Sentry: {message}")
    else:
        logger.info(f"Message captured by Sentry: {message}")


def set_user_context(user_id: str, username: str = None, email: str = None):
    """
    设置用户上下文（用于关联错误与用户）

    Args:
        user_id: 用户ID
        username: 用户名
        email: 邮箱
    """
    if not _sentry_initialized:
        return

    from sentry_sdk import configure_scope
    with configure_scope() as scope:
        scope.set_user({
            'id': user_id,
            'username': username,
            'email': email,
        })


def clear_user_context():
    """清除用户上下文（用户登出时调用）"""
    if not _sentry_initialized:
        return

    from sentry_sdk import configure_scope
    with configure_scope() as scope:
        scope.set_user(None)


def configure_scope():
    """
    配置 Sentry scope 的上下文管理器

    用法:
        with configure_scope() as scope:
            scope.set_tag("key", "value")
            scope.set_extra("key", "value")
    """
    from sentry_sdk import configure_scope as sentry_configure_scope
    return sentry_configure_scope()


def add_breadcrumb(
    category: str,
    message: str,
    level: str = 'info',
    data: Optional[dict] = None
):
    """
    添加面包屑导航（用于追踪用户操作路径）

    Args:
        category: 类别 (e.g., "user", "http", "query")
        message: 消息
        level: 级别 (info, warning, error)
        data: 额外数据
    """
    if not _sentry_initialized:
        return

    from sentry_sdk import add_breadcrumb as sentry_add_breadcrumb
    sentry_add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data=data or {}
    )


def set_transaction(name: str, op: str = 'function'):
    """
    设置性能监控事务名称

    Args:
        name: 事务名称 (e.g., "process_payment", "create_user")
        op: 操作类型 (function, db, http)
    """
    if not _sentry_initialized:
        return

    from sentry_sdk import start_transaction
    return start_transaction(name=name, op=op)


# 装饰器：自动捕获异常并上报
def sentry_captured(
    tags: Optional[dict] = None,
    level: str = 'error'
):
    """
    装饰器：自动捕获函数中的异常并上报到 Sentry

    用法:
        @sentry_captured(tags={'operation': 'payment'})
        async def process_payment():
            ...
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                capture_exception(e, level=level, tags=tags)
                raise

        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                capture_exception(e, level=level, tags=tags)
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 性能监控装饰器
def trace_transaction(name: str = None, op: str = 'function'):
    """
    装饰器：自动追踪函数执行时间

    用法:
        @trace_transaction(name='process_order')
        async def process_order(order_id):
            ...
    """
    def decorator(func):
        transaction_name = name or func.__name__

        async def async_wrapper(*args, **kwargs):
            with set_transaction(transaction_name, op):
                return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            with set_transaction(transaction_name, op):
                return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 初始化 Sentry（在应用启动时调用）
def init_on_startup():
    """
    应用启动时初始化 Sentry

    在 app/main.py 的 lifespan 中调用
    """
    try:
        init_sentry()

        if _sentry_initialized:
            # 添加启动信息
            add_breadcrumb(
                category='app',
                message='Application started',
                level='info',
                data={'module': 'payday-backend'}
            )

            logger.info("Sentry initialized successfully")
        else:
            logger.info("Sentry not configured, running without error tracking")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
