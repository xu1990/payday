"""主题服务测试"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import theme_service
from app.models.theme import Theme, UserSetting
from tests.test_utils import TestDataFactory


class TestListThemes:
    """测试获取主题列表功能"""

    @pytest.mark.asyncio
    async def test_list_themes_empty(self, db_session: AsyncSession):
        """测试空主题列表"""
        themes = await theme_service.list_themes(db_session)

        assert themes == []

    @pytest.mark.asyncio
    async def test_list_themes_system_only(self, db_session: AsyncSession):
        """测试只返回系统主题"""
        # 创建系统主题
        theme1 = Theme(
            name="default",
            display_name="默认主题",
            preview_color="#FFFFFF",
            primary_color="#007AFF",
            is_dark=0,
            is_system=1,
        )
        theme2 = Theme(
            name="dark",
            display_name="暗色主题",
            preview_color="#000000",
            primary_color="#007AFF",
            is_dark=1,
            is_system=1,
        )
        db_session.add(theme1)
        db_session.add(theme2)
        await db_session.commit()

        # 获取主题列表
        themes = await theme_service.list_themes(db_session)

        # 验证返回2个系统主题
        assert len(themes) == 2
        assert all(theme.is_system == 1 for theme in themes)

    @pytest.mark.asyncio
    async def test_list_themes_excludes_user_themes(self, db_session: AsyncSession):
        """测试不包含用户自定义主题"""
        # 创建系统主题
        system_theme = Theme(
            name="default",
            display_name="默认主题",
            preview_color="#FFFFFF",
            primary_color="#007AFF",
            is_dark=0,
            is_system=1,
        )
        # 创建用户主题
        user_theme = Theme(
            name="custom",
            display_name="自定义主题",
            preview_color="#FF0000",
            primary_color="#00FF00",
            is_dark=0,
            is_system=0,
        )
        db_session.add(system_theme)
        db_session.add(user_theme)
        await db_session.commit()

        # 获取主题列表
        themes = await theme_service.list_themes(db_session)

        # 验证只返回系统主题
        assert len(themes) == 1
        assert themes[0].is_system == 1
        assert themes[0].name == "default"

    @pytest.mark.asyncio
    async def test_list_themes_ordered_by_created_at(self, db_session: AsyncSession):
        """测试按创建时间排序"""
        import time

        # 创建多个系统主题
        theme1 = Theme(
            name="theme1",
            display_name="主题1",
            preview_color="#FFFFFF",
            primary_color="#007AFF",
            is_dark=0,
            is_system=1,
        )
        db_session.add(theme1)
        await db_session.commit()
        time.sleep(0.01)

        theme2 = Theme(
            name="theme2",
            display_name="主题2",
            preview_color="#000000",
            primary_color="#FF0000",
            is_dark=1,
            is_system=1,
        )
        db_session.add(theme2)
        await db_session.commit()
        time.sleep(0.01)

        theme3 = Theme(
            name="theme3",
            display_name="主题3",
            preview_color="#CCCCCC",
            primary_color="#00FF00",
            is_dark=0,
            is_system=1,
        )
        db_session.add(theme3)
        await db_session.commit()

        # 获取主题列表
        themes = await theme_service.list_themes(db_session)

        # 验证按创建时间升序排列
        assert len(themes) == 3
        assert themes[0].id == theme1.id
        assert themes[1].id == theme2.id
        assert themes[2].id == theme3.id


class TestGetUserSettings:
    """测试获取用户设置功能"""

    @pytest.mark.asyncio
    async def test_get_user_settings_default(self, db_session: AsyncSession):
        """测试获取默认用户设置"""
        user = await TestDataFactory.create_user(db_session)

        # 获取用户设置（用户还没有设置记录）
        settings = await theme_service.get_user_settings(db_session, user.id)

        # 验证返回默认值
        assert settings["theme_id"] is None
        assert settings["privacy_profile"] == 0
        assert settings["allow_stranger_notice"] == 1
        assert settings["allow_comment"] == 1

    @pytest.mark.asyncio
    async def test_get_user_settings_existing(self, db_session: AsyncSession):
        """测试获取已存在的用户设置"""
        user = await TestDataFactory.create_user(db_session)

        # 创建用户设置
        user_setting = UserSetting(
            user_id=user.id,
            theme_id="test_theme_id",
            privacy_profile=1,
            allow_stranger_notice=0,
            allow_comment=0,
        )
        db_session.add(user_setting)
        await db_session.commit()

        # 获取用户设置
        settings = await theme_service.get_user_settings(db_session, user.id)

        # 验证返回正确值
        assert settings["theme_id"] == "test_theme_id"
        assert settings["privacy_profile"] == 1
        assert settings["allow_stranger_notice"] == 0
        assert settings["allow_comment"] == 0

    @pytest.mark.asyncio
    async def test_get_user_settings_with_null_values(self, db_session: AsyncSession):
        """测试处理NULL值的用户设置"""
        user = await TestDataFactory.create_user(db_session)

        # 创建包含NULL值的设置
        user_setting = UserSetting(
            user_id=user.id,
            theme_id=None,
            privacy_profile=None,
            allow_stranger_notice=None,
            allow_comment=None,
        )
        db_session.add(user_setting)
        await db_session.commit()

        # 获取用户设置
        settings = await theme_service.get_user_settings(db_session, user.id)

        # 验证NULL值被转换为默认值
        assert settings["theme_id"] is None
        assert settings["privacy_profile"] == 0
        assert settings["allow_stranger_notice"] == 1
        assert settings["allow_comment"] == 1

    @pytest.mark.asyncio
    async def test_get_user_settings_isolated(self, db_session: AsyncSession):
        """测试用户设置隔离"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 为user1创建设置
        setting1 = UserSetting(
            user_id=user1.id,
            theme_id="theme1",
            privacy_profile=1,
            allow_stranger_notice=0,
            allow_comment=1,
        )
        db_session.add(setting1)

        # 为user2创建设置
        setting2 = UserSetting(
            user_id=user2.id,
            theme_id="theme2",
            privacy_profile=0,
            allow_stranger_notice=1,
            allow_comment=0,
        )
        db_session.add(setting2)
        await db_session.commit()

        # 获取各自设置
        settings1 = await theme_service.get_user_settings(db_session, user1.id)
        settings2 = await theme_service.get_user_settings(db_session, user2.id)

        # 验证设置隔离
        assert settings1["theme_id"] == "theme1"
        assert settings1["privacy_profile"] == 1

        assert settings2["theme_id"] == "theme2"
        assert settings2["privacy_profile"] == 0


class TestUpdateUserSettings:
    """测试更新用户设置功能"""

    @pytest.mark.asyncio
    async def test_update_user_settings_create_new(self, db_session: AsyncSession):
        """测试更新时创建新设置"""
        user = await TestDataFactory.create_user(db_session)

        # 先创建一个默认主题用于测试
        default_theme = Theme(
            name="默认",
            display_name="默认主题",
            preview_color="#FFFFFF",
            primary_color="#007AFF",
            is_dark=0,
            is_system=1,
        )
        db_session.add(default_theme)
        await db_session.commit()

        # 更新用户设置（首次创建）
        updated = await theme_service.update_user_settings(
            db_session,
            user.id,
            theme_id=default_theme.id,
            privacy_profile=1,
            allow_stranger_notice=0,
            allow_comment=0,
        )

        # 验证创建成功
        assert updated.id is not None
        assert updated.user_id == user.id
        assert updated.theme_id == default_theme.id
        assert updated.privacy_profile == 1
        assert updated.allow_stranger_notice == 0
        assert updated.allow_comment == 0

    @pytest.mark.asyncio
    async def test_update_user_settings_update_existing(self, db_session: AsyncSession):
        """测试更新已存在的设置"""
        user = await TestDataFactory.create_user(db_session)

        # 创建现有设置
        existing = UserSetting(
            user_id=user.id,
            theme_id="old_theme",
            privacy_profile=0,
            allow_stranger_notice=1,
            allow_comment=1,
        )
        db_session.add(existing)
        await db_session.commit()

        # 更新设置
        updated = await theme_service.update_user_settings(
            db_session,
            user.id,
            theme_id="new_theme",
            privacy_profile=1,
        )

        # 验证更新成功
        assert updated.id == existing.id
        assert updated.theme_id == "new_theme"
        assert updated.privacy_profile == 1
        # 未更新的字段保持原值
        assert updated.allow_stranger_notice == 1
        assert updated.allow_comment == 1

    @pytest.mark.asyncio
    async def test_update_user_settings_partial_update(self, db_session: AsyncSession):
        """测试部分更新设置"""
        user = await TestDataFactory.create_user(db_session)

        # 创建现有设置
        existing = UserSetting(
            user_id=user.id,
            theme_id="theme1",
            privacy_profile=0,
            allow_stranger_notice=1,
            allow_comment=1,
        )
        db_session.add(existing)
        await db_session.commit()

        # 只更新theme_id
        updated = await theme_service.update_user_settings(
            db_session,
            user.id,
            theme_id="theme2",
        )

        # 验证只有theme_id被更新
        assert updated.theme_id == "theme2"
        assert updated.privacy_profile == 0
        assert updated.allow_stranger_notice == 1
        assert updated.allow_comment == 1

    @pytest.mark.asyncio
    async def test_update_user_settings_none_values(self, db_session: AsyncSession):
        """测试传入None时不更新对应字段"""
        user = await TestDataFactory.create_user(db_session)

        # 创建现有设置
        existing = UserSetting(
            user_id=user.id,
            theme_id="theme1",
            privacy_profile=1,
            allow_stranger_notice=0,
            allow_comment=0,
        )
        db_session.add(existing)
        await db_session.commit()

        # 传入None（不更新）
        updated = await theme_service.update_user_settings(
            db_session,
            user.id,
            theme_id=None,
            privacy_profile=None,
            allow_stranger_notice=None,
            allow_comment=None,
        )

        # 验证字段未被更新
        assert updated.theme_id == "theme1"
        assert updated.privacy_profile == 1
        assert updated.allow_stranger_notice == 0
        assert updated.allow_comment == 0

    @pytest.mark.asyncio
    async def test_update_user_settings_with_default_theme(self, db_session: AsyncSession):
        """测试创建设置时使用默认主题"""
        user = await TestDataFactory.create_user(db_session)

        # 创建默认主题
        default_theme = Theme(
            name="默认",
            display_name="默认主题",
            preview_color="#FFFFFF",
            primary_color="#007AFF",
            is_dark=0,
            is_system=1,
        )
        db_session.add(default_theme)
        await db_session.commit()

        # 更新时不指定theme_id（应该使用默认主题）
        updated = await theme_service.update_user_settings(
            db_session,
            user.id,
            privacy_profile=1,
        )

        # 验证使用默认主题
        assert updated.theme_id == default_theme.id
        assert updated.privacy_profile == 1

    @pytest.mark.asyncio
    async def test_update_user_settings_isolation(self, db_session: AsyncSession):
        """测试用户设置更新隔离"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 为user1创建设置
        setting1 = UserSetting(
            user_id=user1.id,
            theme_id="theme1",
            privacy_profile=0,
            allow_stranger_notice=1,
            allow_comment=1,
        )
        db_session.add(setting1)

        # 为user2创建设置
        setting2 = UserSetting(
            user_id=user2.id,
            theme_id="theme2",
            privacy_profile=1,
            allow_stranger_notice=0,
            allow_comment=0,
        )
        db_session.add(setting2)
        await db_session.commit()

        # 更新user1的设置
        await theme_service.update_user_settings(
            db_session,
            user1.id,
            theme_id="new_theme1",
        )

        # 刷新user2的设置
        await db_session.refresh(setting2)

        # 验证user2的设置未被影响
        assert setting2.theme_id == "theme2"
        assert setting2.privacy_profile == 1

    @pytest.mark.asyncio
    async def test_update_user_settings_all_fields(self, db_session: AsyncSession):
        """测试更新所有字段"""
        user = await TestDataFactory.create_user(db_session)

        # 创建设置
        existing = UserSetting(
            user_id=user.id,
            theme_id="old_theme",
            privacy_profile=0,
            allow_stranger_notice=1,
            allow_comment=1,
        )
        db_session.add(existing)
        await db_session.commit()

        # 更新所有字段
        updated = await theme_service.update_user_settings(
            db_session,
            user.id,
            theme_id="new_theme",
            privacy_profile=1,
            allow_stranger_notice=0,
            allow_comment=0,
        )

        # 验证所有字段都已更新
        assert updated.theme_id == "new_theme"
        assert updated.privacy_profile == 1
        assert updated.allow_stranger_notice == 0
        assert updated.allow_comment == 0


class TestGetDefaultThemeId:
    """测试获取默认主题ID功能（私有函数）"""

    @pytest.mark.asyncio
    async def test_get_default_theme_id_exists(self, db_session: AsyncSession):
        """测试获取存在的默认主题ID"""
        # 创建默认主题
        default_theme = Theme(
            name="默认",
            display_name="默认主题",
            preview_color="#FFFFFF",
            primary_color="#007AFF",
            is_dark=0,
            is_system=1,
        )
        db_session.add(default_theme)
        await db_session.commit()

        # 获取默认主题ID（通过调用update_user_settings间接测试）
        user = await TestDataFactory.create_user(db_session)
        updated = await theme_service.update_user_settings(db_session, user.id)

        # 验证使用了默认主题
        assert updated.theme_id == default_theme.id

    @pytest.mark.asyncio
    async def test_get_default_theme_id_not_exists(self, db_session: AsyncSession):
        """测试默认主题不存在时返回空字符串"""
        # 不创建任何主题，直接创建用户设置
        user = await TestDataFactory.create_user(db_session)
        updated = await theme_service.update_user_settings(db_session, user.id)

        # 验证theme_id为空字符串（当默认主题不存在时）
        assert updated.theme_id == ""


class TestThemeSettingsWorkflow:
    """测试主题设置完整流程"""

    @pytest.mark.asyncio
    async def test_user_theme_selection_workflow(self, db_session: AsyncSession):
        """测试用户选择主题的完整流程"""
        user = await TestDataFactory.create_user(db_session)

        # 1. 创建系统主题
        default_theme = Theme(
            name="默认",
            display_name="默认主题",
            preview_color="#FFFFFF",
            primary_color="#007AFF",
            is_dark=0,
            is_system=1,
        )
        dark_theme = Theme(
            name="暗色",
            display_name="暗色主题",
            preview_color="#000000",
            primary_color="#FFFFFF",
            is_dark=1,
            is_system=1,
        )
        db_session.add(default_theme)
        db_session.add(dark_theme)
        await db_session.commit()

        # 2. 获取主题列表
        themes = await theme_service.list_themes(db_session)
        assert len(themes) == 2

        # 3. 获取用户初始设置（默认）
        settings = await theme_service.get_user_settings(db_session, user.id)
        assert settings["theme_id"] is None

        # 4. 用户选择默认主题
        await theme_service.update_user_settings(
            db_session,
            user.id,
            theme_id=default_theme.id,
        )

        # 5. 验证设置已更新
        settings = await theme_service.get_user_settings(db_session, user.id)
        assert settings["theme_id"] == default_theme.id

        # 6. 用户切换到暗色主题
        await theme_service.update_user_settings(
            db_session,
            user.id,
            theme_id=dark_theme.id,
        )

        # 7. 验证主题已切换
        settings = await theme_service.get_user_settings(db_session, user.id)
        assert settings["theme_id"] == dark_theme.id

    @pytest.mark.asyncio
    async def test_user_privacy_settings_workflow(self, db_session: AsyncSession):
        """测试用户隐私设置流程"""
        user = await TestDataFactory.create_user(db_session)

        # 1. 获取初始设置
        settings = await theme_service.get_user_settings(db_session, user.id)
        assert settings["privacy_profile"] == 0  # 公开
        assert settings["allow_stranger_notice"] == 1  # 允许
        assert settings["allow_comment"] == 1  # 允许

        # 2. 更新为仅好友可见
        await theme_service.update_user_settings(
            db_session,
            user.id,
            privacy_profile=1,
        )
        settings = await theme_service.get_user_settings(db_session, user.id)
        assert settings["privacy_profile"] == 1

        # 3. 禁用陌生人私信
        await theme_service.update_user_settings(
            db_session,
            user.id,
            allow_stranger_notice=0,
        )
        settings = await theme_service.get_user_settings(db_session, user.id)
        assert settings["allow_stranger_notice"] == 0

        # 4. 禁用评论
        await theme_service.update_user_settings(
            db_session,
            user.id,
            allow_comment=0,
        )
        settings = await theme_service.get_user_settings(db_session, user.id)
        assert settings["allow_comment"] == 0

    @pytest.mark.asyncio
    async def test_multiple_users_different_settings(self, db_session: AsyncSession):
        """测试多个用户使用不同设置"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")

        # 创建主题
        theme1 = Theme(
            name="theme1",
            display_name="主题1",
            preview_color="#FFFFFF",
            primary_color="#007AFF",
            is_dark=0,
            is_system=1,
        )
        theme2 = Theme(
            name="theme2",
            display_name="主题2",
            preview_color="#000000",
            primary_color="#FF0000",
            is_dark=1,
            is_system=1,
        )
        db_session.add(theme1)
        db_session.add(theme2)
        await db_session.commit()

        # user1使用theme1，隐私设置严格
        await theme_service.update_user_settings(
            db_session,
            user1.id,
            theme_id=theme1.id,
            privacy_profile=1,
            allow_stranger_notice=0,
            allow_comment=0,
        )

        # user2使用theme2，隐私设置开放
        await theme_service.update_user_settings(
            db_session,
            user2.id,
            theme_id=theme2.id,
            privacy_profile=0,
            allow_stranger_notice=1,
            allow_comment=1,
        )

        # 验证各自设置
        settings1 = await theme_service.get_user_settings(db_session, user1.id)
        settings2 = await theme_service.get_user_settings(db_session, user2.id)

        assert settings1["theme_id"] == theme1.id
        assert settings1["privacy_profile"] == 1
        assert settings1["allow_stranger_notice"] == 0

        assert settings2["theme_id"] == theme2.id
        assert settings2["privacy_profile"] == 0
        assert settings2["allow_stranger_notice"] == 1

    @pytest.mark.asyncio
    async def test_settings_persistence(self, db_session: AsyncSession):
        """测试设置持久化"""
        user = await TestDataFactory.create_user(db_session)

        # 创建主题
        theme = Theme(
            name="test",
            display_name="测试主题",
            preview_color="#FFFFFF",
            primary_color="#007AFF",
            is_dark=0,
            is_system=1,
        )
        db_session.add(theme)
        await db_session.commit()

        # 第一次更新设置
        await theme_service.update_user_settings(
            db_session,
            user.id,
            theme_id=theme.id,
            privacy_profile=1,
            allow_stranger_notice=0,
            allow_comment=1,
        )

        # 多次读取验证一致性
        for _ in range(3):
            settings = await theme_service.get_user_settings(db_session, user.id)
            assert settings["theme_id"] == theme.id
            assert settings["privacy_profile"] == 1
            assert settings["allow_stranger_notice"] == 0
            assert settings["allow_comment"] == 1
