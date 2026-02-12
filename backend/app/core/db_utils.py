"""
数据库事务管理工具 - 提供统一的事务处理模式
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')


@asynccontextmanager
async def transaction(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    数据库事务上下文管理器

    用法:
        async with transaction(db):
            db.add(entity)
            # 自动提交或回滚
    """
    async with db.begin():
        yield db


async def commit_or_rollback(db: AsyncSession) -> None:
    """
    显式提交或回滚（用于需要精细控制的场景）

    注意：推荐使用 transaction() 上下文管理器
    """
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise


class TransactionalMixin:
    """
    事务混入类 - 为 Service 类提供事务支持

    用法:
        class MyService(TransactionalMixin):
            async def create_item(self, db, data):
                async with self.transaction(db):
                    item = Item(**data)
                    db.add(item)
                    await db.flush(item)
                return item
    """

    @staticmethod
    @asynccontextmanager
    async def transaction(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
        """创建事务上下文"""
        async with db.begin():
            yield db
