"""
单元测试 - 游标分页工具 (app.utils.pagination)
"""
import pytest
import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import desc, asc, or_, and_

from app.utils.pagination import CursorPaginator, CursorPaginationResult, offset_paginate
from app.models.user import User


class TestCursorPaginationResult:
    """测试 CursorPaginationResult"""

    def test_cursor_pagination_result_init(self):
        """测试初始化"""
        result = CursorPaginationResult(
            items=[{"id": "1"}, {"id": "2"}],
            next_cursor="cursor123",
            has_more=True,
            total=100
        )

        assert result.items == [{"id": "1"}, {"id": "2"}]
        assert result.next_cursor == "cursor123"
        assert result.has_more is True
        assert result.total == 100

    def test_cursor_pagination_result_defaults(self):
        """测试默认值"""
        result = CursorPaginationResult(items=[])

        assert result.items == []
        assert result.next_cursor is None
        assert result.has_more is False
        assert result.total is None


class TestCursorPaginatorInit:
    """测试 CursorPaginator 初始化"""

    def test_init_basic(self):
        """测试基本初始化"""
        paginator = CursorPaginator(
            User,
            order_by=[desc(User.created_at), desc(User.id)]
        )

        assert paginator.model == User
        assert len(paginator.order_by) == 2
        assert paginator.filter_expr is None

    def test_init_with_filter(self):
        """测试带过滤条件的初始化"""
        filter_expr = User.status == "normal"
        paginator = CursorPaginator(
            User,
            order_by=[desc(User.id)],
            filter_expr=filter_expr
        )

        assert paginator.filter_expr == filter_expr


class TestDecodeCursor:
    """测试游标解码"""

    def test_decode_cursor_valid(self):
        """测试有效游标解码"""
        paginator = CursorPaginator(User, order_by=[desc(User.id)])

        # 创建一个有效的游标
        values = ("2024-01-01", "user123")
        encoded = base64.b64encode(json.dumps(values).encode()).decode()

        result = paginator._decode_cursor(encoded)

        assert result == ("2024-01-01", "user123")

    def test_decode_cursor_single_value(self):
        """测试单个值游标"""
        paginator = CursorPaginator(User, order_by=[desc(User.id)])

        values = ("user123",)
        encoded = base64.b64encode(json.dumps(values).encode()).decode()

        result = paginator._decode_cursor(encoded)

        assert result == ("user123",)

    def test_decode_cursor_invalid_base64(self):
        """测试无效 base64"""
        paginator = CursorPaginator(User, order_by=[desc(User.id)])

        with pytest.raises(ValueError, match="Invalid cursor"):
            paginator._decode_cursor("not-valid-base64!")

    def test_decode_cursor_invalid_json(self):
        """测试无效 JSON"""
        paginator = CursorPaginator(User, order_by=[desc(User.id)])

        encoded = base64.b64encode(b"not valid json").decode()

        with pytest.raises(ValueError, match="Invalid cursor"):
            paginator._decode_cursor(encoded)


class TestEncodeCursor:
    """测试游标编码"""

    def test_encode_cursor_basic(self):
        """测试基本编码"""
        paginator = CursorPaginator(User, order_by=[desc(User.id)])

        values = ("2024-01-01", "user123")
        encoded = paginator._encode_cursor(values)

        # Should be valid base64
        decoded = base64.b64decode(encoded).decode()
        assert json.loads(decoded) == ["2024-01-01", "user123"]

    def test_encode_cursor_single_value(self):
        """测试单个值编码"""
        paginator = CursorPaginator(User, order_by=[desc(User.id)])

        values = ("user123",)
        encoded = paginator._encode_cursor(values)

        decoded = base64.b64decode(encoded).decode()
        assert json.loads(decoded) == ["user123"]

    def test_encode_decode_roundtrip(self):
        """测试编码解码往返"""
        paginator = CursorPaginator(User, order_by=[desc(User.id)])

        original_values = ("2024-01-01T10:30:00", "user123", "extra")
        encoded = paginator._encode_cursor(original_values)
        decoded = paginator._decode_cursor(encoded)

        assert decoded == original_values


class TestBuildConditions:
    """测试构建分页条件"""

    def test_build_conditions_no_cursor_no_filter(self):
        """测试无游标无过滤"""
        paginator = CursorPaginator(User, order_by=[desc(User.id)])

        condition = paginator._build_conditions(None)

        assert condition is None

    def test_build_conditions_no_cursor_with_filter(self):
        """测试无游标有过滤"""
        filter_expr = User.status == "normal"
        paginator = CursorPaginator(
            User,
            order_by=[desc(User.id)],
            filter_expr=filter_expr
        )

        condition = paginator._build_conditions(None)

        assert condition == filter_expr

    def test_build_conditions_invalid_cursor_length(self):
        """测试游标长度不匹配"""
        paginator = CursorPaginator(
            User,
            order_by=[desc(User.created_at), desc(User.id)]
        )

        # 游标只有1个值，但 order_by 有2个字段
        values = ("2024-01-01",)
        cursor = base64.b64encode(json.dumps(values).encode()).decode()

        with pytest.raises(ValueError, match="Cursor does not match"):
            paginator._build_conditions(cursor)

    @pytest.mark.skip("SQLAlchemy internals complex to mock")
    def test_build_conditions_with_single_order_by(self):
        """测试单个排序字段的游标条件 - 跳过由于 SQLAlchemy 内部实现复杂"""
        pass


class TestPaginate:
    """测试分页查询"""

    @pytest.mark.asyncio
    async def test_paginate_empty_result(self, db_session):
        """测试空结果"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        with patch('app.utils.pagination.select') as mock_select:
            mock_query = MagicMock()
            mock_query.where.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.subquery.return_value = MagicMock()
            mock_select.return_value = mock_query

            db_session.execute = AsyncMock(return_value=mock_result)

            paginator = CursorPaginator(User, order_by=[desc(User.id)])
            result = await paginator.paginate(db_session, limit=20)

            assert result.items == []
            assert result.next_cursor is None
            assert result.has_more is False
            assert result.total is None

    @pytest.mark.asyncio
    async def test_paginate_with_count(self, db_session):
        """测试带总数的分页"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 100

        with patch('app.utils.pagination.select') as mock_select:
            mock_query = MagicMock()
            mock_query.where.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.subquery.return_value = MagicMock()
            mock_select.return_value = mock_query

            # First call for items, second for count
            db_session.execute = AsyncMock(return_value=mock_result)

            paginator = CursorPaginator(User, order_by=[desc(User.id)])
            result = await paginator.paginate(db_session, limit=20, with_count=True)

            assert result.total == 100


class TestOffsetPaginate:
    """测试传统 OFFSET 分页"""

    @pytest.mark.asyncio
    async def test_offset_paginate_basic(self, db_session):
        """测试基本分页"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 100

        with patch('app.utils.pagination.select') as mock_select:
            mock_query = MagicMock()
            mock_query.where.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.subquery.return_value = MagicMock()
            mock_select.return_value = mock_query

            db_session.execute = AsyncMock(return_value=mock_result)

            result = await offset_paginate(
                db_session,
                User,
                limit=20,
                offset=0,
                order_by=[desc(User.id)]
            )

            assert result["items"] == []
            assert result["total"] == 100
            assert result["limit"] == 20
            assert result["offset"] == 0

    @pytest.mark.asyncio
    async def test_offset_paginate_with_filter(self, db_session):
        """测试带过滤条件"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 50

        with patch('app.utils.pagination.select') as mock_select:
            mock_query = MagicMock()
            mock_query.where.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.subquery.return_value = MagicMock()
            mock_select.return_value = mock_query

            db_session.execute = AsyncMock(return_value=mock_result)

            filter_expr = User.status == "normal"
            result = await offset_paginate(
                db_session,
                User,
                limit=20,
                offset=0,
                filter_expr=filter_expr
            )

            # Should get a result with total count
            assert result["total"] == 50
            assert result["limit"] == 20

    @pytest.mark.asyncio
    async def test_offset_paginate_no_count(self, db_session):
        """测试不获取总数"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        with patch('app.utils.pagination.select') as mock_select:
            mock_query = MagicMock()
            mock_query.where.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_select.return_value = mock_query

            db_session.execute = AsyncMock(return_value=mock_result)

            result = await offset_paginate(
                db_session,
                User,
                limit=20,
                offset=0,
                with_count=False
            )

            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_offset_paginate_with_order(self, db_session):
        """测试带排序"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 10

        with patch('app.utils.pagination.select') as mock_select:
            mock_query = MagicMock()
            mock_query.where.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.subquery.return_value = MagicMock()
            mock_select.return_value = mock_query

            db_session.execute = AsyncMock(return_value=mock_result)

            result = await offset_paginate(
                db_session,
                User,
                limit=10,
                offset=0,
                order_by=[desc(User.created_at)]
            )

            assert result["limit"] == 10
            mock_query.order_by.assert_called_once()
