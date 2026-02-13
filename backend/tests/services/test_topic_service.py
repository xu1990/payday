"""话题服务测试"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.topic_service import (
    create_topic,
    get_topic_by_id,
    list_topics,
    update_topic,
    delete_topic,
    increment_post_count,
    decrement_post_count,
)
from app.models.topic import Topic
from app.core.exceptions import NotFoundException


class TestCreateTopic:
    """测试创建话题"""

    @pytest.mark.asyncio
    async def test_create_topic_success(self, db_session: AsyncSession):
        """测试成功创建话题"""
        topic = await create_topic(
            db_session,
            name="测试话题",
            description="这是一个测试话题",
            sort_order=10,
        )

        assert topic.id is not None
        assert topic.name == "测试话题"
        assert topic.description == "这是一个测试话题"
        assert topic.sort_order == 10
        assert topic.is_active == True
        assert topic.post_count == 0

    @pytest.mark.asyncio
    async def test_create_topic_with_cover_image(self, db_session: AsyncSession):
        """测试创建带封面图的话题"""
        topic = await create_topic(
            db_session,
            name="封面话题",
            cover_image="https://example.com/cover.jpg",
        )

        assert topic.cover_image == "https://example.com/cover.jpg"

    @pytest.mark.asyncio
    async def test_create_topic_default_values(self, db_session: AsyncSession):
        """测试创建话题的默认值"""
        topic = await create_topic(db_session, name="默认话题")

        assert topic.is_active == True
        assert topic.post_count == 0
        assert topic.sort_order == 0
        assert topic.description is None
        assert topic.cover_image is None


class TestGetTopicById:
    """测试获取单个话题"""

    @pytest.mark.asyncio
    async def test_get_existing_topic(self, db_session: AsyncSession):
        """测试获取已存在的话题"""
        created = await create_topic(db_session, name="测试话题")

        found = await get_topic_by_id(db_session, created.id)

        assert found is not None
        assert found.id == created.id
        assert found.name == "测试话题"

    @pytest.mark.asyncio
    async def test_get_nonexistent_topic(self, db_session: AsyncSession):
        """测试获取不存在的话题返回None"""
        found = await get_topic_by_id(db_session, "nonexistent_id")
        assert found is None


class TestListTopics:
    """测试获取话题列表"""

    @pytest.mark.asyncio
    async def test_list_all_topics(self, db_session: AsyncSession):
        """测试获取所有话题"""
        await create_topic(db_session, name="话题1", sort_order=10)
        await create_topic(db_session, name="话题2", sort_order=5)

        topics, total = await list_topics(db_session)

        assert total == 2
        assert len(topics) == 2

    @pytest.mark.asyncio
    async def test_list_active_only(self, db_session: AsyncSession):
        """测试仅获取启用的话题"""
        topic1 = await create_topic(db_session, name="启用话题")
        topic2 = await create_topic(db_session, name="禁用话题")
        # 禁用第二个话题
        await update_topic(db_session, topic2.id, is_active=False)

        topics, total = await list_topics(db_session, active_only=True)

        assert total == 1
        assert len(topics) == 1
        assert topics[0].name == "启用话题"

    @pytest.mark.asyncio
    async def test_list_order_by_sort_order_desc(self, db_session: AsyncSession):
        """测试按排序权重倒序排列"""
        await create_topic(db_session, name="话题1", sort_order=10)
        await create_topic(db_session, name="话题2", sort_order=30)
        await create_topic(db_session, name="话题3", sort_order=20)

        topics, total = await list_topics(db_session)

        assert topics[0].sort_order == 30
        assert topics[1].sort_order == 20
        assert topics[2].sort_order == 10

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, db_session: AsyncSession):
        """测试分页功能"""
        for i in range(5):
            await create_topic(db_session, name=f"话题{i}", sort_order=i)

        # 第一页：2条
        topics1, total1 = await list_topics(db_session, limit=2, offset=0)
        assert total1 == 5
        assert len(topics1) == 2

        # 第二页：2条
        topics2, total2 = await list_topics(db_session, limit=2, offset=2)
        assert total2 == 5
        assert len(topics2) == 2

        # 第三页：1条
        topics3, total3 = await list_topics(db_session, limit=2, offset=4)
        assert total3 == 5
        assert len(topics3) == 1

    @pytest.mark.asyncio
    async def test_list_empty_result(self, db_session: AsyncSession):
        """测试空结果"""
        topics, total = await list_topics(db_session)
        assert total == 0
        assert topics == []


class TestUpdateTopic:
    """测试更新话题"""

    @pytest.mark.asyncio
    async def test_update_name(self, db_session: AsyncSession):
        """测试更新名称"""
        topic = await create_topic(db_session, name="原名称")

        updated = await update_topic(db_session, topic.id, name="新名称")

        assert updated.name == "新名称"

    @pytest.mark.asyncio
    async def test_update_description(self, db_session: AsyncSession):
        """测试更新描述"""
        topic = await create_topic(db_session, name="测试话题")

        updated = await update_topic(db_session, topic.id, description="新描述")

        assert updated.description == "新描述"

    @pytest.mark.asyncio
    async def test_update_cover_image(self, db_session: AsyncSession):
        """测试更新封面图"""
        topic = await create_topic(db_session, name="测试话题")

        updated = await update_topic(
            db_session, topic.id, cover_image="https://example.com/new.jpg"
        )

        assert updated.cover_image == "https://example.com/new.jpg"

    @pytest.mark.asyncio
    async def test_update_is_active(self, db_session: AsyncSession):
        """测试更新启用状态"""
        topic = await create_topic(db_session, name="测试话题")

        updated = await update_topic(db_session, topic.id, is_active=False)

        assert updated.is_active == False

    @pytest.mark.asyncio
    async def test_update_sort_order(self, db_session: AsyncSession):
        """测试更新排序权重"""
        topic = await create_topic(db_session, name="测试话题", sort_order=0)

        updated = await update_topic(db_session, topic.id, sort_order=100)

        assert updated.sort_order == 100

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, db_session: AsyncSession):
        """测试同时更新多个字段"""
        topic = await create_topic(db_session, name="原名称", sort_order=0)

        updated = await update_topic(
            db_session,
            topic.id,
            name="新名称",
            description="新描述",
            sort_order=50,
            is_active=False,
        )

        assert updated.name == "新名称"
        assert updated.description == "新描述"
        assert updated.sort_order == 50
        assert updated.is_active == False

    @pytest.mark.asyncio
    async def test_update_none_values_no_change(self, db_session: AsyncSession):
        """测试传入None值不修改字段"""
        topic = await create_topic(
            db_session, name="测试话题", description="原描述", sort_order=10
        )

        updated = await update_topic(db_session, topic.id, name=None, description=None)

        # 字段应保持不变
        assert updated.name == "测试话题"
        assert updated.description == "原描述"

    @pytest.mark.asyncio
    async def test_update_nonexistent_topic_raises_exception(self, db_session: AsyncSession):
        """测试更新不存在的话题抛出异常"""
        with pytest.raises(NotFoundException) as exc_info:
            await update_topic(db_session, "nonexistent_id", name="新名称")

        assert "不存在" in str(exc_info.value)


class TestDeleteTopic:
    """测试删除话题"""

    @pytest.mark.asyncio
    async def test_delete_topic_success(self, db_session: AsyncSession):
        """测试成功删除话题"""
        topic = await create_topic(db_session, name="测试话题")

        result = await delete_topic(db_session, topic.id)

        assert result is True

        # 验证已删除
        deleted = await get_topic_by_id(db_session, topic.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_topic(self, db_session: AsyncSession):
        """测试删除不存在的话题返回False"""
        result = await delete_topic(db_session, "nonexistent_id")
        assert result is False


class TestIncrementPostCount:
    """测试增加帖子计数"""

    @pytest.mark.asyncio
    async def test_increment_post_count(self, db_session: AsyncSession):
        """测试增加帖子计数"""
        topic = await create_topic(db_session, name="测试话题")

        result = await increment_post_count(db_session, topic.id)

        assert result is True

        # 验证计数已增加
        updated = await get_topic_by_id(db_session, topic.id)
        assert updated.post_count == 1

    @pytest.mark.asyncio
    async def test_increment_multiple_times(self, db_session: AsyncSession):
        """测试多次增加"""
        topic = await create_topic(db_session, name="测试话题")

        await increment_post_count(db_session, topic.id)
        await increment_post_count(db_session, topic.id)
        await increment_post_count(db_session, topic.id)

        updated = await get_topic_by_id(db_session, topic.id)
        assert updated.post_count == 3

    @pytest.mark.asyncio
    async def test_increment_nonexistent_topic(self, db_session: AsyncSession):
        """测试对不存在的话题增加计数"""
        result = await increment_post_count(db_session, "nonexistent_id")
        assert result is False


class TestDecrementPostCount:
    """测试减少帖子计数"""

    @pytest.mark.asyncio
    async def test_decrement_post_count(self, db_session: AsyncSession):
        """测试减少帖子计数"""
        topic = await create_topic(db_session, name="测试话题")

        # 先增加
        await increment_post_count(db_session, topic.id)

        # 再减少
        result = await decrement_post_count(db_session, topic.id)

        assert result is True

        # 验证计数已减少
        updated = await get_topic_by_id(db_session, topic.id)
        assert updated.post_count == 0

    @pytest.mark.asyncio
    async def test_decrement_below_zero(self, db_session: AsyncSession):
        """测试减少到零时不再减少"""
        topic = await create_topic(db_session, name="测试话题")

        # 尝试减少（应该是0）
        result = await decrement_post_count(db_session, topic.id)

        assert result is True

        # 验证计数不会低于0
        updated = await get_topic_by_id(db_session, topic.id)
        assert updated.post_count == 0

    @pytest.mark.asyncio
    async def test_decrement_nonexistent_topic(self, db_session: AsyncSession):
        """测试对不存在的话题减少计数"""
        result = await decrement_post_count(db_session, "nonexistent_id")
        assert result is False
