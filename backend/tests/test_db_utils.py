"""
单元测试 - 数据库事务管理工具 (app.core.db_utils)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_utils import transaction, commit_or_rollback, TransactionalMixin


class TestTransaction:
    """测试事务上下文管理器"""

    @pytest.mark.asyncio
    async def test_transaction_success(self):
        """测试成功事务"""
        mock_db = MagicMock(spec=AsyncSession)
        mock_begin = AsyncMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_db)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_db.begin = MagicMock(return_value=mock_begin)

        async with transaction(mock_db) as session:
            assert session is mock_db

        mock_db.begin.assert_called_once()
        mock_begin.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_exception(self):
        """测试异常时事务回滚"""
        mock_db = MagicMock(spec=AsyncSession)
        mock_begin = AsyncMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_db)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_db.begin = MagicMock(return_value=mock_begin)

        with pytest.raises(ValueError):
            async with transaction(mock_db) as session:
                raise ValueError("Test error")

        # __aexit__ should still be called
        mock_begin.__aexit__.assert_called_once()


class TestCommitOrRollback:
    """测试提交或回滚函数"""

    @pytest.mark.asyncio
    async def test_commit_success(self):
        """测试成功提交"""
        mock_db = MagicMock(spec=AsyncSession)
        mock_db.commit = AsyncMock(return_value=None)

        await commit_or_rollback(mock_db)

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_on_exception(self):
        """测试异常时回滚"""
        mock_db = MagicMock(spec=AsyncSession)
        mock_db.commit = AsyncMock(side_effect=Exception("DB error"))
        mock_db.rollback = AsyncMock(return_value=None)

        with pytest.raises(Exception) as exc_info:
            await commit_or_rollback(mock_db)

        assert "DB error" in str(exc_info.value)
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_called_once()


class TestTransactionalMixin:
    """测试事务混入类"""

    @pytest.mark.asyncio
    async def test_transaction_context_manager(self):
        """测试混入类的事务上下文管理器"""
        mock_db = MagicMock(spec=AsyncSession)
        mock_begin = AsyncMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_db)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_db.begin = MagicMock(return_value=mock_begin)

        mixin = TransactionalMixin()

        async with mixin.transaction(mock_db) as session:
            assert session is mock_db

        mock_db.begin.assert_called_once()
