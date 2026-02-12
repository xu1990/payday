"""
数据库连接与会话 - 技术方案 2.2
支持同步和异步会话
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .config import get_settings

settings = get_settings()

# 同步引擎（用于 Alembic 迁移）
sync_engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug,
)

# 同步会话（用于 Alembic）
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

# 异步引擎和会话（延迟初始化，避免导入时错误）
_async_engine = None
_AsyncSessionLocal = None


def _get_async_engine():
    """获取或创建异步引擎（延迟初始化）"""
    global _async_engine, _AsyncSessionLocal
    if _async_engine is None:
        async_database_url = settings.database_url.replace("mysql+pymysql://", "mysql+aiomysql://")
        _async_engine = create_async_engine(
            async_database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.debug,
        )
        _AsyncSessionLocal = async_sessionmaker(
            bind=_async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_engine


async def get_db():
    """异步会话依赖"""
    _get_async_engine()
    async with _AsyncSessionLocal() as session:
        yield session
