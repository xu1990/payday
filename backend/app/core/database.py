"""
数据库连接与会话 - 技术方案 2.2 + 性能优化
支持同步和异步会话，优化连接池配置
技术方案 4.2.2 - 数据库连接池优化
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .config import get_settings

settings = get_settings()

# 同步引擎（用于 Alembic 迁移）
# 技术方案 4.2.2 - 连接池配置优化
sync_engine = create_engine(
    settings.database_url,
    # 连接池配置
    pool_size=20,              # 连接池大小
    max_overflow=40,           # 最大溢出连接数
    pool_pre_ping=True,         # 连接前检测
    pool_recycle=3600,          # 连接回收时间(秒)
    # 性能优化
    echo=settings.debug,
    connect_args={
        "charset": "utf8mb4",
        "connect_timeout": 10,
    },
)

# 同步会话（用于 Alembic）
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# 兼容性别名
SessionLocal = SyncSessionLocal

Base = declarative_base()

# 异步引擎和会话（延迟初始化，避免导入时错误）
_async_engine = None
_AsyncSessionLocal = None

# 导出给外部使用（初始化后可用）
async_session_maker = None


def _get_async_engine():
    """获取或创建异步引擎（延迟初始化）"""
    global _async_engine, _AsyncSessionLocal, async_session_maker
    if _async_engine is None:
        async_database_url = settings.database_url.replace("mysql+pymysql://", "mysql+aiomysql://")
        # 技术方案 4.2.2 - 异步连接池配置优化
        _async_engine = create_async_engine(
            async_database_url,
            # 连接池配置
            pool_size=20,              # 连接池大小
            max_overflow=40,           # 最大溢出连接数
            pool_pre_ping=True,         # 连接前检测
            pool_recycle=3600,          # 连接回收时间(秒)
            # 性能优化
            echo=settings.debug,
            connect_args={
                "charset": "utf8mb4",
                "connect_timeout": 10,
            },
        )
        _AsyncSessionLocal = async_sessionmaker(
            bind=_async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async_session_maker = _AsyncSessionLocal
    return _async_engine


async def get_db():
    """异步会话依赖"""
    _get_async_engine()
    async with _AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def transactional(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    事务管理上下文管理器 - 自动提交或回滚

    Usage:
        async with transactional(db) as session:
            session.add(user)
            # 自动提交或异常时回滚

    Args:
        db: AsyncSession 实例

    Yields:
        AsyncSession: 同一个会话实例

    Raises:
        Exception: 事务中的任何异常都会触发回滚并重新抛出
    """
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise

