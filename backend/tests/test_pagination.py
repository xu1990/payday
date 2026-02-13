"""分页工具测试"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.utils.pagination import (
    CursorPaginator,
    CursorPaginationResult,
    offset_paginate,
)
from app.models.user import User
from app.models.post import Post
from tests.test_utils import TestDataFactory


class TestCursorEncodeDecode:
    """测试游标编解码"""

    def test_encode_decode_single_value(self):
        """测试编解码单个值"""
        paginator = CursorPaginator(User, order_by=[User.id])
        values = (1,)

        cursor = paginator._encode_cursor(values)
        decoded = paginator._decode_cursor(cursor)

        assert decoded == values

    def test_encode_decode_multiple_values(self):
        """测试编解码多个值"""
        paginator = CursorPaginator(Post, order_by=[Post.created_at, Post.id])
        timestamp = "2024-01-01T00:00:00"
        values = (timestamp, "post_id_123")

        cursor = paginator._encode_cursor(values)
        decoded = paginator._decode_cursor(cursor)

        assert decoded == values

    def test_decode_invalid_cursor(self):
        """测试解码无效游标"""
        paginator = CursorPaginator(User, order_by=[User.id])

        with pytest.raises(ValueError, match="Invalid cursor"):
            paginator._decode_cursor("invalid_base64!!!")

    def test_cursor_stability(self):
        """测试相同值产生相同游标"""
        paginator = CursorPaginator(User, order_by=[User.id])
        values = (123,)

        cursor1 = paginator._encode_cursor(values)
        cursor2 = paginator._encode_cursor(values)

        assert cursor1 == cursor2


class TestOffsetPaginate:
    """测试传统OFFSET分页"""

    @pytest.mark.asyncio
    async def test_first_page(self, db_session: AsyncSession):
        """测试第一页"""
        # 创建测试数据
        for i in range(5):
            await TestDataFactory.create_user(db_session)

        result = await offset_paginate(db_session, User, limit=2, offset=0)

        assert len(result["items"]) == 2
        assert result["total"] == 5
        assert result["limit"] == 2
        assert result["offset"] == 0

    @pytest.mark.asyncio
    async def test_second_page(self, db_session: AsyncSession):
        """测试第二页"""
        # 创建测试数据
        for i in range(5):
            await TestDataFactory.create_user(db_session)

        result = await offset_paginate(db_session, User, limit=2, offset=2)

        assert len(result["items"]) == 2
        assert result["offset"] == 2

    @pytest.mark.asyncio
    async def test_last_page_partial(self, db_session: AsyncSession):
        """测试最后一页（不满）"""
        # 创建3条数据
        for i in range(3):
            await TestDataFactory.create_user(db_session)

        result = await offset_paginate(db_session, User, limit=2, offset=2)

        assert len(result["items"]) == 1
        assert result["total"] == 3

    @pytest.mark.asyncio
    async def test_beyond_last_page(self, db_session: AsyncSession):
        """测试超出最后一页"""
        # 创建2条数据
        for i in range(2):
            await TestDataFactory.create_user(db_session)

        result = await offset_paginate(db_session, User, limit=2, offset=10)

        assert len(result["items"]) == 0
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_with_order_by(self, db_session: AsyncSession):
        """测试带排序"""
        for i in range(5):
            await TestDataFactory.create_user(db_session, anonymous_name=f"用户{i}")

        result = await offset_paginate(
            db_session,
            User,
            limit=10,
            offset=0,
            order_by=[User.anonymous_name]
        )

        assert len(result["items"]) == 5
        # 验证排序
        names = [item["anonymous_name"] for item in result["items"]]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_with_filter(self, db_session: AsyncSession):
        """测试带过滤条件"""
        # 创建测试数据
        for i in range(3):
            await TestDataFactory.create_post(
                db_session,
                user_id=f"user_{i}",
                content=f"内容{i}",
                status="normal",
                risk_status="approved"
            )

        # 使用一个具体的过滤条件
        result = await offset_paginate(
            db_session,
            Post,
            limit=10,
            offset=0,
            filter_expr=Post.status == "normal"
        )

        assert len(result["items"]) == 3
        assert result["total"] == 3

    @pytest.mark.asyncio
    async def test_without_count(self, db_session: AsyncSession):
        """测试不返回总数"""
        for i in range(5):
            await TestDataFactory.create_user(db_session)

        result = await offset_paginate(
            db_session,
            User,
            limit=2,
            offset=0,
            with_count=False
        )

        assert len(result["items"]) == 2
        assert result["total"] == 0  # with_count=False 返回0

    @pytest.mark.asyncio
    async def test_items_are_dicts(self, db_session: AsyncSession):
        """测试返回的items是字典"""
        await TestDataFactory.create_user(db_session)

        result = await offset_paginate(db_session, User, limit=10)

        assert isinstance(result["items"], list)
        if result["items"]:
            assert isinstance(result["items"][0], dict)
            assert "id" in result["items"][0]


class TestCursorPaginatorBasic:
    """测试游标分页器 - 基础功能"""

    @pytest.mark.asyncio
    async def test_encode_cursor_single_value(self, db_session: AsyncSession):
        """测试单值游标编码"""
        paginator = CursorPaginator(User, order_by=[User.id])
        cursor = paginator._encode_cursor(("user123",))

        assert cursor is not None
        assert isinstance(cursor, str)

    @pytest.mark.asyncio
    async def test_decode_valid_cursor(self, db_session: AsyncSession):
        """测试解码有效游标"""
        paginator = CursorPaginator(User, order_by=[User.id])
        original_value = ("user123",)
        cursor = paginator._encode_cursor(original_value)

        decoded = paginator._decode_cursor(cursor)

        assert decoded == original_value

    @pytest.mark.asyncio
    async def test_decode_invalid_cursor_raises_error(self, db_session: AsyncSession):
        """测试解码无效游标抛出错误"""
        paginator = CursorPaginator(User, order_by=[User.id])

        with pytest.raises(ValueError, match="Invalid cursor"):
            paginator._decode_cursor("not_a_valid_cursor")

    @pytest.mark.asyncio
    async def test_empty_result(self, db_session: AsyncSession):
        """测试空结果集"""
        # 创建用户但使用特定过滤条件使其返回空
        await TestDataFactory.create_user(db_session, status="normal")

        # 使用会过滤掉所有数据的条件
        from sqlalchemy import false
        paginator = CursorPaginator(User, order_by=[User.id], filter_expr=false())
        result = await paginator.paginate(db_session, limit=10)

        assert len(result.items) == 0
        assert result.has_more is False
        assert result.next_cursor is None

    @pytest.mark.asyncio
    async def test_items_contain_expected_fields(self, db_session: AsyncSession):
        """测试返回的items包含预期字段"""
        await TestDataFactory.create_user(db_session, anonymous_name="测试用户")

        # 简单分页，不使用游标
        result = await offset_paginate(db_session, User, limit=10)

        assert isinstance(result["items"], list)
        if result["items"]:
            item = result["items"][0]
            assert "id" in item
            assert "anonymous_name" in item

    @pytest.mark.asyncio
    async def test_result_model_structure(self, db_session: AsyncSession):
        """测试结果模型结构"""
        await TestDataFactory.create_user(db_session)

        result = await offset_paginate(db_session, User, limit=10)

        # 验证返回结构
        assert "items" in result
        assert "total" in result
        assert "limit" in result
        assert "offset" in result
        assert isinstance(result["items"], list)
        assert isinstance(result["total"], int)
