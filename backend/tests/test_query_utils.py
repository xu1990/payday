"""
单元测试 - 查询优化工具 (app.core.query_utils)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.query_utils import QueryHelper, get_or_404
from app.core.exceptions import NotFoundException
from app.models.user import User


class TestQueryHelper:
    """测试查询辅助类"""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, db_session):
        """测试按ID查找实体 - 找到"""
        from tests.test_utils import TestDataFactory

        user = await TestDataFactory.create_user(db_session)

        result = await QueryHelper.get_by_id(db_session, User, str(user.id))

        assert result is not None
        assert result.id == user.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session):
        """测试按ID查找实体 - 未找到"""
        result = await QueryHelper.get_by_id(db_session, User, "nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_with_for_update(self, db_session):
        """测试按ID查找实体 - 带行锁"""
        from tests.test_utils import TestDataFactory

        user = await TestDataFactory.create_user(db_session)

        result = await QueryHelper.get_by_id(
            db_session, User, str(user.id), with_for_update=True
        )

        assert result is not None
        assert result.id == user.id

    @pytest.mark.asyncio
    async def test_get_by_id_with_eager_loads(self, db_session):
        """测试按ID查找实体 - 带预加载"""
        from tests.test_utils import TestDataFactory
        from sqlalchemy.orm import selectinload

        user = await TestDataFactory.create_user(db_session)

        # 测试预加载（即使没有关系，也应该正常工作）
        result = await QueryHelper.get_by_id(
            db_session, User, str(user.id), eager_loads=[]
        )

        assert result is not None
        assert result.id == user.id

    @pytest.mark.asyncio
    async def test_list_with_pagination_default(self, db_session):
        """测试分页查询 - 默认参数"""
        from tests.test_utils import TestDataFactory

        # 创建多个用户
        for _ in range(5):
            await TestDataFactory.create_user(db_session)

        items, total = await QueryHelper.list_with_pagination(
            db_session, User
        )

        assert len(items) == 5
        assert total == 5

    @pytest.mark.asyncio
    async def test_list_with_pagination_with_limit(self, db_session):
        """测试分页查询 - 自定义限制"""
        from tests.test_utils import TestDataFactory

        # 创建多个用户
        for _ in range(10):
            await TestDataFactory.create_user(db_session)

        items, total = await QueryHelper.list_with_pagination(
            db_session, User, limit=3
        )

        assert len(items) == 3
        assert total == 10

    @pytest.mark.asyncio
    async def test_list_with_pagination_with_offset(self, db_session):
        """测试分页查询 - 带偏移"""
        from tests.test_utils import TestDataFactory

        # 创建多个用户
        for _ in range(10):
            await TestDataFactory.create_user(db_session)

        items, total = await QueryHelper.list_with_pagination(
            db_session, User, limit=5, offset=5
        )

        assert len(items) == 5
        assert total == 10

    @pytest.mark.asyncio
    async def test_list_with_pagination_empty_result(self, db_session):
        """测试分页查询 - 空结果"""
        items, total = await QueryHelper.list_with_pagination(
            db_session, User
        )

        assert len(items) == 0
        assert total == 0


class TestGetOr404:
    """测试获取实体或404函数"""

    @pytest.mark.asyncio
    async def test_get_or_404_found(self, db_session):
        """测试获取实体 - 找到"""
        from tests.test_utils import TestDataFactory

        user = await TestDataFactory.create_user(db_session)

        result = await get_or_404(db_session, User, str(user.id))

        assert result.id == user.id

    @pytest.mark.asyncio
    async def test_get_or_404_not_found(self, db_session):
        """测试获取实体 - 未找到（抛出404）"""
        with pytest.raises(NotFoundException) as exc_info:
            await get_or_404(db_session, User, "nonexistent_id")
        assert "资源不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_or_404_custom_error_message(self, db_session):
        """测试获取实体 - 自定义错误消息"""
        with pytest.raises(NotFoundException) as exc_info:
            await get_or_404(
                db_session, User, "nonexistent_id",
                error_message="用户不存在"
            )
        assert "用户不存在" in str(exc_info.value)
