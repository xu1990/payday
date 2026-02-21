"""
数据库连接与会话 - 技术方案 2.2 + 性能优化
支持同步和异步会话，优化连接池配置
技术方案 4.2.2 - 数据库连接池优化
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from .config import get_settings

nullpool = NullPool

settings = get_settings()


def _get_connect_args():
    """根据数据库类型返回连接参数"""
    db_url = settings.effective_database_url
    if db_url.startswith("sqlite"):
        # SQLite: 启用外键约束支持
        return {
            "check_same_thread": False,
        }
    else:
        # MySQL 连接参数
        return {
            "charset": "utf8mb4",
            "connect_timeout": 10,
        }


def _get_pool_config():
    """根据数据库类型返回连接池配置"""
    db_url = settings.effective_database_url
    if db_url.startswith("sqlite"):
        # SQLite 不需要连接池
        return {
            "poolclass": nullpool,  # SQLite 使用空连接池
        }
    else:
        # MySQL 连接池配置
        return {
            "pool_size": 20,
            "max_overflow": 40,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }


# 同步引擎（用于 Alembic 迁移）
# 技术方案 4.2.2 - 连接池配置优化
sync_engine = create_engine(
    settings.effective_database_url,
    # 连接池配置
    **_get_pool_config(),
    # 性能优化
    echo=settings.debug,
    connect_args=_get_connect_args(),
)


# 为 SQLite 启用外键约束（同步引擎）
@event.listens_for(sync_engine, "connect")
def set_sqlite_pragma_sync(dbapi_conn, connection_record):
    """为每个新的 SQLite 连接启用外键约束"""
    if settings.effective_database_url.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
        db_url = settings.effective_database_url

        # 转换为异步驱动 URL
        if db_url.startswith("mysql+pymysql://"):
            async_database_url = db_url.replace("mysql+pymysql://", "mysql+aiomysql://")
        elif db_url.startswith("sqlite://"):
            # SQLite: 启用外键支持
            async_database_url = db_url.replace("sqlite://", "sqlite+aiosqlite://") + "?uri=true"
        else:
            async_database_url = db_url

        # 技术方案 4.2.2 - 异步连接池配置优化
        _async_engine = create_async_engine(
            async_database_url,
            # 连接池配置
            **_get_pool_config(),
            # 性能优化
            echo=settings.debug,
            connect_args=_get_connect_args(),
        )

        # 为 SQLite 启用外键约束（异步引擎）
        if db_url.startswith("sqlite://"):
            # 异步引擎的底层同步引擎
            from sqlalchemy import exc as sqla_exc

            @event.listens_for(_async_engine.sync_engine, "connect")
            def set_sqlite_pragma_async(dbapi_conn, connection_record):
                """为每个新的 SQLite 连接启用外键约束"""
                cursor = dbapi_conn.cursor()
                try:
                    cursor.execute("PRAGMA foreign_keys=ON")
                except sqla_exc.DBAPIError as e:
                    # 如果 PRAGMA 执行失败，记录警告但不中断连接
                    if "syntax error" not in str(e):
                        print(f"Warning: Failed to enable SQLite foreign keys: {e}")
                finally:
                    cursor.close()

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

