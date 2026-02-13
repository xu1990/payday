"""
单元测试 - 查询优化工具 (app.core.query_utils)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from app.core.query_utils import QueryHelper, get_or_404
from app.core.exceptions import NotFoundException
from app.models.user import User


class TestQueryHelperGetById:
    """测试 QueryHelper.get_by_id 方法"""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, db_session):
        """测试查找到实体"""
        mock_result = MagicMock()
        mock_user = User(id="test_id", anonymous_name="Test User")
        mock_result.scalar_one_or_none.return_value = mock_user

        with patch.object(db_session, 'execute', return_value=mock_result) as mock_execute:
            result = await QueryHelper.get_by_id(db_session, User, "test_id")

            assert result.id == "test_id"
            assert result.anonymous_name == "Test User"
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session):
        """测试未找到实体"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(db_session, 'execute', return_value=mock_result):
            result = await QueryHelper.get_by_id(db_session, User, "nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_with_for_update(self, db_session):
        """测试带行锁的查询"""
        mock_result = MagicMock()
        mock_user = User(id="test_id")
        mock_result.scalar_one_or_none.return_value = mock_user

        with patch.object(db_session, 'execute', return_value=mock_result) as mock_execute:
            result = await QueryHelper.get_by_id(
                db_session,
                User,
                "test_id",
                with_for_update=True
            )

            # Verify execute was called
            assert mock_execute.called
            # The query should have with_for_update applied
            call_args = mock_execute.call_args
            query = call_args[0][0]
            # Query should be a select object
            assert query is not None

    @pytest.mark.asyncio
    async def test_get_by_id_with_eager_loads(self, db_session):
        """测试带预加载的查询 - 验证代码执行无异常"""
        mock_result = MagicMock()
        mock_user = User(id="test_id")
        mock_result.scalar_one_or_none.return_value = mock_user

        # Patch the entire select function to return a chainable mock
        from sqlalchemy import select as real_select

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        # Create a mock that chains properly
        mock_select = MagicMock()
        mock_select.where.return_value = mock_select
        mock_select.options.return_value = mock_select
        mock_select.with_for_update.return_value = mock_select

        with patch('app.core.query_utils.select', return_value=mock_select):
            result = await QueryHelper.get_by_id(
                db_session,
                User,
                "test_id",
                eager_loads=[MagicMock()]
            )

            # Verify the result is returned correctly
            assert result.id == "test_id"


class TestQueryHelperListWithPagination:
    """测试 QueryHelper.list_with_pagination 方法"""

    @pytest.mark.asyncio
    async def test_list_with_pagination_basic(self, db_session):
        """测试基本分页查询"""
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100

        # Mock list query
        mock_list_result = MagicMock()
        mock_scalars = MagicMock()
        mock_users = [
            User(id="1", anonymous_name="User1"),
            User(id="2", anonymous_name="User2"),
        ]
        mock_scalars.all.return_value = mock_users
        mock_list_result.scalars.return_value = mock_scalars

        with patch.object(db_session, 'execute', side_effect=[mock_count_result, mock_list_result]) as mock_execute:
            items, total = await QueryHelper.list_with_pagination(
                db_session,
                User,
                limit=10,
                offset=0
            )

            assert len(items) == 2
            assert total == 100
            assert mock_execute.call_count == 2

    @pytest.mark.asyncio
    async def test_list_with_pagination_with_filters(self, db_session):
        """测试带过滤条件的分页查询"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50

        mock_list_result = MagicMock()
        mock_scalars = MagicMock()
        mock_users = [User(id="1", anonymous_name="User1")]
        mock_scalars.all.return_value = mock_users
        mock_list_result.scalars.return_value = mock_scalars

        with patch.object(db_session, 'execute', side_effect=[mock_count_result, mock_list_result]):
            from sqlalchemy import or_
            mock_filter = or_(User.anonymous_name == "Test")

            items, total = await QueryHelper.list_with_pagination(
                db_session,
                User,
                limit=10,
                offset=0,
                filters=[mock_filter]
            )

            assert total == 50
            assert len(items) == 1

    @pytest.mark.asyncio
    async def test_list_with_pagination_empty_result(self, db_session):
        """测试空结果"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_list_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_list_result.scalars.return_value = mock_scalars

        with patch.object(db_session, 'execute', side_effect=[mock_count_result, mock_list_result]):
            items, total = await QueryHelper.list_with_pagination(
                db_session,
                User
            )

            assert items == []
            assert total == 0

    @pytest.mark.asyncio
    async def test_list_with_pagination_count_none(self, db_session):
        """测试count返回None"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = None

        mock_list_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_list_result.scalars.return_value = mock_scalars

        with patch.object(db_session, 'execute', side_effect=[mock_count_result, mock_list_result]):
            items, total = await QueryHelper.list_with_pagination(
                db_session,
                User
            )

            # Should default to 0 when count is None
            assert total == 0

    @pytest.mark.asyncio
    async def test_list_with_pagination_with_order(self, db_session):
        """测试带排序的分页查询"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10

        mock_list_result = MagicMock()
        mock_scalars = MagicMock()
        mock_users = [User(id="1", anonymous_name="User1")]
        mock_scalars.all.return_value = mock_users
        mock_list_result.scalars.return_value = mock_scalars

        with patch.object(db_session, 'execute', side_effect=[mock_count_result, mock_list_result]):
            from sqlalchemy import desc
            mock_order = desc(User.created_at)

            items, total = await QueryHelper.list_with_pagination(
                db_session,
                User,
                order_by=mock_order
            )

            assert total == 10

    @pytest.mark.asyncio
    async def test_list_with_pagination_with_eager_loads(self, db_session):
        """测试带预加载的分页查询"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10

        mock_list_result = MagicMock()
        mock_scalars = MagicMock()
        mock_users = [User(id="1", anonymous_name="User1")]
        mock_scalars.all.return_value = mock_users
        mock_list_result.scalars.return_value = mock_scalars

        with patch.object(db_session, 'execute', side_effect=[mock_count_result, mock_list_result]):
            # Create a mock select object that can handle options()
            mock_query = MagicMock()

            with patch('app.core.query_utils.select', return_value=mock_query):
                mock_loader = MagicMock()

                items, total = await QueryHelper.list_with_pagination(
                    db_session,
                    User,
                    eager_loads=[mock_loader]
                )

                # Verify options was called with the loader
                mock_query.options.assert_called_once_with(mock_loader)


class TestGetOr404:
    """测试 get_or_404 函数"""

    @pytest.mark.asyncio
    async def test_get_or_404_found(self, db_session):
        """测试找到实体"""
        mock_result = MagicMock()
        mock_user = User(id="test_id")
        mock_result.scalar_one_or_none.return_value = mock_user

        with patch.object(db_session, 'execute', return_value=mock_result):
            result = await get_or_404(db_session, User, "test_id")

            assert result.id == "test_id"

    @pytest.mark.asyncio
    async def test_get_or_404_not_found(self, db_session):
        """测试实体不存在抛出404"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(db_session, 'execute', return_value=mock_result):
            with pytest.raises(NotFoundException) as exc_info:
                await get_or_404(db_session, User, "nonexistent")

            assert "资源不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_or_404_custom_error_message(self, db_session):
        """测试自定义错误消息"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(db_session, 'execute', return_value=mock_result):
            with pytest.raises(NotFoundException) as exc_info:
                await get_or_404(
                    db_session,
                    User,
                    "nonexistent",
                    error_message="用户不存在"
                )

            assert "用户不存在" in str(exc_info.value)
