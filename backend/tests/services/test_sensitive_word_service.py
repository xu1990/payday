"""敏感词服务测试"""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.sensitive_word_service import (
    list_words,
    get_word_by_id,
    create_word,
    update_word,
    delete_word,
    get_active_words_dict,
    get_all_active_words_list,
)
from app.models.sensitive_word import SensitiveWord
from app.core.exceptions import NotFoundException, BusinessException


class TestListWords:
    """测试获取敏感词列表"""

    @pytest.mark.asyncio
    async def test_list_all_words(self, db_session: AsyncSession):
        """测试获取所有敏感词"""
        # 使用服务函数创建测试数据
        await create_word(db_session, "毒品", "illegal")
        await create_word(db_session, "赌博", "illegal")

        # 创建禁用的词
        word_id = str(uuid.uuid4()).replace("-", "")
        word3 = SensitiveWord(id=word_id, word="色情", category="porn", is_active=False)
        db_session.add(word3)
        await db_session.commit()

        # 获取所有词
        words = await list_words(db_session)

        assert len(words) == 3

    @pytest.mark.asyncio
    async def test_list_by_category(self, db_session: AsyncSession):
        """测试按分类筛选"""
        await create_word(db_session, "毒品", "illegal")
        await create_word(db_session, "色情", "porn")

        words = await list_words(db_session, category="illegal")

        assert len(words) == 1
        assert words[0].word == "毒品"

    @pytest.mark.asyncio
    async def test_list_by_active_status(self, db_session: AsyncSession):
        """测试按启用状态筛选"""
        await create_word(db_session, "毒品", "illegal")

        word_id = str(uuid.uuid4()).replace("-", "")
        word2 = SensitiveWord(id=word_id, word="赌博", category="illegal", is_active=False)
        db_session.add(word2)
        await db_session.commit()

        words = await list_words(db_session, is_active=True)

        assert len(words) == 1
        assert words[0].word == "毒品"

    @pytest.mark.asyncio
    async def test_list_by_both_filters(self, db_session: AsyncSession):
        """测试同时使用分类和状态筛选"""
        await create_word(db_session, "毒品", "illegal")
        await create_word(db_session, "色情", "porn")

        word_id = str(uuid.uuid4()).replace("-", "")
        word3 = SensitiveWord(id=word_id, word="赌博", category="illegal", is_active=False)
        db_session.add(word3)
        await db_session.commit()

        words = await list_words(db_session, category="illegal", is_active=True)

        assert len(words) == 1
        assert words[0].word == "毒品"

    @pytest.mark.asyncio
    async def test_list_empty_result(self, db_session: AsyncSession):
        """测试空结果"""
        words = await list_words(db_session)
        assert len(words) == 0

    @pytest.mark.asyncio
    async def test_list_order_by_created_at_desc(self, db_session: AsyncSession):
        """测试按创建时间倒序排列"""
        import time

        word1 = await create_word(db_session, "毒品", "illegal")
        time.sleep(0.01)  # 确保创建时间不同
        word2 = await create_word(db_session, "赌博", "illegal")

        words = await list_words(db_session)

        # 最后创建的应排在前面
        assert words[0].word == "赌博"
        assert words[1].word == "毒品"


class TestGetWordById:
    """测试根据ID获取敏感词"""

    @pytest.mark.asyncio
    async def test_get_existing_word(self, db_session: AsyncSession):
        """测试获取已存在的敏感词"""
        word = await create_word(db_session, "毒品", "illegal")

        found_word = await get_word_by_id(db_session, word.id)

        assert found_word is not None
        assert found_word.id == word.id
        assert found_word.word == "毒品"

    @pytest.mark.asyncio
    async def test_get_nonexistent_word(self, db_session: AsyncSession):
        """测试获取不存在的敏感词返回None"""
        word = await get_word_by_id(db_session, "nonexistent_id")
        assert word is None


class TestCreateWord:
    """测试创建敏感词"""

    @pytest.mark.asyncio
    async def test_create_word_success(self, db_session: AsyncSession):
        """测试成功创建敏感词"""
        word = await create_word(db_session, "毒品", "illegal")

        assert word.id is not None
        assert word.word == "毒品"
        assert word.category == "illegal"

    @pytest.mark.asyncio
    async def test_create_duplicate_word_raises_exception(self, db_session: AsyncSession):
        """测试创建重复敏感词抛出异常"""
        # 创建第一个词
        await create_word(db_session, "毒品", "illegal")

        # 尝试创建相同词汇
        with pytest.raises(BusinessException) as exc_info:
            await create_word(db_session, "毒品", "illegal")

        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_word_default_active(self, db_session: AsyncSession):
        """测试创建敏感词默认启用"""
        word = await create_word(db_session, "毒品", "illegal")

        assert word.is_active == 1


class TestUpdateWord:
    """测试更新敏感词"""

    @pytest.mark.asyncio
    async def test_update_word_text(self, db_session: AsyncSession):
        """测试更新敏感词文本"""
        word = await create_word(db_session, "毒品", "illegal")

        updated_word = await update_word(db_session, word.id, word="毒品2")

        assert updated_word.word == "毒品2"

    @pytest.mark.asyncio
    async def test_update_word_category(self, db_session: AsyncSession):
        """测试更新分类"""
        word = await create_word(db_session, "毒品", "illegal")

        updated_word = await update_word(db_session, word.id, category="porn")

        assert updated_word.category == "porn"

    @pytest.mark.asyncio
    async def test_update_word_is_active(self, db_session: AsyncSession):
        """测试更新启用状态"""
        word = await create_word(db_session, "毒品", "illegal")

        updated_word = await update_word(db_session, word.id, is_active=False)

        assert updated_word.is_active == False

    @pytest.mark.asyncio
    async def test_update_word_multiple_fields(self, db_session: AsyncSession):
        """测试同时更新多个字段"""
        word = await create_word(db_session, "毒品", "illegal")

        updated_word = await update_word(
            db_session,
            word.id,
            word="毒品2",
            category="porn",
            is_active=False
        )

        assert updated_word.word == "毒品2"
        assert updated_word.category == "porn"
        assert updated_word.is_active == False

    @pytest.mark.asyncio
    async def test_update_word_none_values_no_change(self, db_session: AsyncSession):
        """测试传入None值不修改字段"""
        word = await create_word(db_session, "毒品", "illegal")

        updated_word = await update_word(db_session, word.id, word=None, category=None)

        # 字段应保持不变
        assert updated_word.word == "毒品"
        assert updated_word.category == "illegal"

    @pytest.mark.asyncio
    async def test_update_nonexistent_word_raises_exception(self, db_session: AsyncSession):
        """测试更新不存在的敏感词抛出异常"""
        with pytest.raises(NotFoundException) as exc_info:
            await update_word(db_session, "nonexistent_id", word="新词")

        assert "不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_to_duplicate_word_raises_exception(self, db_session: AsyncSession):
        """测试更新为已存在的敏感词抛出异常"""
        word1 = await create_word(db_session, "毒品", "illegal")
        word2 = await create_word(db_session, "赌博", "illegal")

        # 尝试将word2更新为word1的词
        with pytest.raises(BusinessException) as exc_info:
            await update_word(db_session, word2.id, word="毒品")

        assert "已存在" in str(exc_info.value)


class TestDeleteWord:
    """测试删除敏感词"""

    @pytest.mark.asyncio
    async def test_delete_word_success(self, db_session: AsyncSession):
        """测试成功删除敏感词"""
        word = await create_word(db_session, "毒品", "illegal")

        result = await delete_word(db_session, word.id)

        assert result is True

        # 验证已删除
        deleted_word = await get_word_by_id(db_session, word.id)
        assert deleted_word is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_word(self, db_session: AsyncSession):
        """测试删除不存在的敏感词返回False"""
        result = await delete_word(db_session, "nonexistent_id")
        assert result is False


class TestGetActiveWordsDict:
    """测试获取启用敏感词字典"""

    @pytest.mark.asyncio
    async def test_get_words_dict(self, db_session: AsyncSession):
        """测试获取分类组织的敏感词字典"""
        await create_word(db_session, "毒品", "illegal")
        await create_word(db_session, "赌博", "illegal")
        await create_word(db_session, "色情", "porn")

        # 创建禁用的词
        word_id = str(uuid.uuid4()).replace("-", "")
        word4 = SensitiveWord(id=word_id, word="暴力", category="violent", is_active=False)
        db_session.add(word4)
        await db_session.commit()

        result = await get_active_words_dict(db_session)

        assert "illegal" in result
        assert "porn" in result
        assert "violent" not in result  # 未启用的分类
        assert "毒品" in result["illegal"]
        assert "赌博" in result["illegal"]
        assert "色情" in result["porn"]

    @pytest.mark.asyncio
    async def test_get_words_dict_empty(self, db_session: AsyncSession):
        """测试空结果"""
        result = await get_active_words_dict(db_session)
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_words_dict_only_active(self, db_session: AsyncSession):
        """测试只包含启用的敏感词"""
        await create_word(db_session, "毒品", "illegal")

        # 创建禁用的词
        word_id = str(uuid.uuid4()).replace("-", "")
        word2 = SensitiveWord(id=word_id, word="赌博", category="illegal", is_active=False)
        db_session.add(word2)
        await db_session.commit()

        result = await get_active_words_dict(db_session)

        assert len(result["illegal"]) == 1
        assert "毒品" in result["illegal"]


class TestGetAllActiveWordsList:
    """测试获取所有启用敏感词列表"""

    @pytest.mark.asyncio
    async def test_get_all_active_words(self, db_session: AsyncSession):
        """测试获取所有启用的敏感词"""
        await create_word(db_session, "毒品", "illegal")
        await create_word(db_session, "赌博", "illegal")

        # 创建禁用的词
        word_id = str(uuid.uuid4()).replace("-", "")
        word3 = SensitiveWord(id=word_id, word="色情", category="porn", is_active=False)
        db_session.add(word3)
        await db_session.commit()

        words = await get_all_active_words_list(db_session)

        assert len(words) == 2
        assert "毒品" in words
        assert "赌博" in words
        assert "色情" not in words

    @pytest.mark.asyncio
    async def test_get_all_active_words_empty(self, db_session: AsyncSession):
        """测试空结果"""
        words = await get_all_active_words_list(db_session)
        assert words == []

    @pytest.mark.asyncio
    async def test_get_all_active_words_no_duplicates(self, db_session: AsyncSession):
        """测试返回的列表无重复"""
        await create_word(db_session, "毒品", "illegal")
        await create_word(db_session, "赌博", "illegal")

        words = await get_all_active_words_list(db_session)

        # 检查无重复
        assert len(words) == len(set(words))
