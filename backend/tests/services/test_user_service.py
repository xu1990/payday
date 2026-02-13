"""用户服务测试"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import (
    get_user_by_id,
    update_user,
    get_user_profile_data,
    list_users_for_admin,
)
from app.models.user import User
from app.models.post import Post
from app.models.checkin import CheckIn
from app.models.follow import Follow
from app.schemas.user import UserUpdate
from app.core.exceptions import NotFoundException
from tests.test_utils import TestDataFactory


class TestGetUserById:
    """测试根据ID获取用户"""

    @pytest.mark.asyncio
    async def test_get_existing_user(self, db_session: AsyncSession):
        """测试获取已存在的用户"""
        # 创建用户
        user = await TestDataFactory.create_user(
            db_session,
            anonymous_name="测试用户001"
        )

        # 查询用户
        found_user = await get_user_by_id(db_session, user.id)

        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.anonymous_name == "测试用户001"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, db_session: AsyncSession):
        """测试获取不存在的用户返回None"""
        # 使用不存在的UUID
        fake_id = "00000000-0000-0000-0000-000000000000"

        user = await get_user_by_id(db_session, fake_id)

        assert user is None


class TestUpdateUser:
    """测试更新用户信息"""

    @pytest.mark.asyncio
    async def test_update_user_anonymous_name(self, db_session: AsyncSession):
        """测试更新用户昵称"""
        user = await TestDataFactory.create_user(
            db_session,
            anonymous_name="旧昵称"
        )

        # 更新昵称
        update_data = UserUpdate(anonymous_name="新昵称")
        updated_user = await update_user(db_session, user.id, update_data)

        assert updated_user.id == user.id
        assert updated_user.anonymous_name == "新昵称"

    @pytest.mark.asyncio
    async def test_update_user_bio(self, db_session: AsyncSession):
        """测试更新用户简介"""
        user = await TestDataFactory.create_user(db_session)

        # 更新简介
        update_data = UserUpdate(bio="这是我的新简介")
        updated_user = await update_user(db_session, user.id, update_data)

        assert updated_user.id == user.id
        assert updated_user.bio == "这是我的新简介"

    @pytest.mark.asyncio
    async def test_update_user_multiple_fields(self, db_session: AsyncSession):
        """测试同时更新多个字段"""
        user = await TestDataFactory.create_user(
            db_session,
            anonymous_name="原昵称"
        )

        # 更新多个字段
        update_data = UserUpdate(
            anonymous_name="更新后的昵称",
            bio="更新后的简介",
            avatar="https://example.com/new-avatar.jpg"
        )
        updated_user = await update_user(db_session, user.id, update_data)

        assert updated_user.id == user.id
        assert updated_user.anonymous_name == "更新后的昵称"
        assert updated_user.bio == "更新后的简介"
        assert updated_user.avatar == "https://example.com/new-avatar.jpg"

    @pytest.mark.asyncio
    async def test_update_user_no_fields(self, db_session: AsyncSession):
        """测试不更新任何字段（空update_data）"""
        user = await TestDataFactory.create_user(
            db_session,
            anonymous_name="原始昵称",
            bio="原始简介"
        )

        # 不传递任何更新字段
        update_data = UserUpdate()
        updated_user = await update_user(db_session, user.id, update_data)

        # 用户信息应保持不变
        assert updated_user.id == user.id
        assert updated_user.anonymous_name == "原始昵称"
        assert updated_user.bio == "原始简介"

    @pytest.mark.asyncio
    async def test_update_nonexistent_user_raises_exception(self, db_session: AsyncSession):
        """测试更新不存在的用户抛出NotFoundException"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = UserUpdate(anonymous_name="新昵称")

        with pytest.raises(NotFoundException) as exc_info:
            await update_user(db_session, fake_id, update_data)

        assert "用户不存在" in str(exc_info.value)


class TestGetUserProfileData:
    """测试获取用户主页数据"""

    @pytest.mark.asyncio
    async def test_get_profile_data_with_posts(self, db_session: AsyncSession):
        """测试获取包含帖子的用户主页数据"""
        user = await TestDataFactory.create_user(db_session)

        # 创建3篇帖子
        for i in range(3):
            await TestDataFactory.create_post(
                db_session,
                user.id,
                content=f"测试内容{i}",
                status="normal",
                risk_status="approved"
            )

        # 获取主页数据
        profile_data = await get_user_profile_data(
            db_session,
            user.id,
            user.id
        )

        assert "posts" in profile_data
        assert "checkins" in profile_data
        assert "follower_count" in profile_data
        assert "following_count" in profile_data
        assert len(profile_data["posts"]) == 3

    @pytest.mark.asyncio
    async def test_get_profile_data_with_checkins(self, db_session: AsyncSession):
        """测试获取包含打卡记录的用户主页数据"""
        from datetime import date

        user = await TestDataFactory.create_user(db_session)

        # 创建5条打卡记录
        for i in range(5):
            checkin = CheckIn(
                user_id=user.id,
                check_date=date(2025, 1, i + 1),
            )
            db_session.add(checkin)
        await db_session.commit()

        # 获取主页数据
        profile_data = await get_user_profile_data(
            db_session,
            user.id,
            user.id
        )

        assert len(profile_data["checkins"]) == 5

    @pytest.mark.asyncio
    async def test_get_profile_data_with_followers(self, db_session: AsyncSession):
        """测试获取包含粉丝数的用户主页数据"""
        user = await TestDataFactory.create_user(db_session)

        # 创建3个粉丝
        for i in range(3):
            follower = await TestDataFactory.create_user(db_session)
            follow = Follow(
                follower_id=follower.id,
                following_id=user.id,
            )
            db_session.add(follow)
        await db_session.commit()

        # 获取主页数据
        profile_data = await get_user_profile_data(
            db_session,
            user.id,
            user.id
        )

        assert profile_data["follower_count"] == 3

    @pytest.mark.asyncio
    async def test_get_profile_data_with_following(self, db_session: AsyncSession):
        """测试获取包含关注数的用户主页数据"""
        user = await TestDataFactory.create_user(db_session)

        # 关注3个用户
        for i in range(3):
            following = await TestDataFactory.create_user(db_session)
            follow = Follow(
                follower_id=user.id,
                following_id=following.id,
            )
            db_session.add(follow)
        await db_session.commit()

        # 获取主页数据
        profile_data = await get_user_profile_data(
            db_session,
            user.id,
            user.id
        )

        assert profile_data["following_count"] == 3

    @pytest.mark.asyncio
    async def test_get_profile_data_counts_all_follows(self, db_session: AsyncSession):
        """测试关注计数统计所有关注关系"""
        user = await TestDataFactory.create_user(db_session)

        # 创建2个粉丝
        follower1 = await TestDataFactory.create_user(db_session)
        follow1 = Follow(
            follower_id=follower1.id,
            following_id=user.id,
        )
        db_session.add(follow1)

        follower2 = await TestDataFactory.create_user(db_session)
        follow2 = Follow(
            follower_id=follower2.id,
            following_id=user.id,
        )
        db_session.add(follow2)
        await db_session.commit()

        # 获取主页数据
        profile_data = await get_user_profile_data(
            db_session,
            user.id,
            user.id
        )

        # 应统计所有关注
        assert profile_data["follower_count"] == 2

    @pytest.mark.asyncio
    async def test_get_profile_data_only_normal_posts(self, db_session: AsyncSession):
        """测试只返回状态为normal的帖子"""
        user = await TestDataFactory.create_user(db_session)

        # 创建不同状态的帖子
        await TestDataFactory.create_post(
            db_session,
            user.id,
            content="正常帖子",
            status="normal",
            risk_status="approved"
        )
        await TestDataFactory.create_post(
            db_session,
            user.id,
            content="已删除帖子",
            status="deleted",
            risk_status="approved"
        )
        await TestDataFactory.create_post(
            db_session,
            user.id,
            content="待审核帖子",
            status="normal",
            risk_status="pending"
        )

        # 获取主页数据
        profile_data = await get_user_profile_data(
            db_session,
            user.id,
            user.id
        )

        # 应只返回状态为normal且风险审核通过的帖子
        assert len(profile_data["posts"]) == 1

    @pytest.mark.asyncio
    async def test_get_profile_data_posts_limited_to_20(self, db_session: AsyncSession):
        """测试帖子数量限制为20条"""
        user = await TestDataFactory.create_user(db_session)

        # 创建25篇帖子
        for i in range(25):
            await TestDataFactory.create_post(
                db_session,
                user.id,
                content=f"测试内容{i}",
                status="normal",
                risk_status="approved"
            )

        # 获取主页数据
        profile_data = await get_user_profile_data(
            db_session,
            user.id,
            user.id
        )

        # 应只返回20条帖子
        assert len(profile_data["posts"]) == 20

    @pytest.mark.asyncio
    async def test_get_profile_data_checkins_limited_to_30(self, db_session: AsyncSession):
        """测试打卡记录限制为30条"""
        from datetime import date

        user = await TestDataFactory.create_user(db_session)

        # 创建35条打卡记录
        for i in range(35):
            checkin = CheckIn(
                user_id=user.id,
                check_date=date(2025, 1, (i % 31) + 1),
            )
            db_session.add(checkin)
        await db_session.commit()

        # 获取主页数据
        profile_data = await get_user_profile_data(
            db_session,
            user.id,
            user.id
        )

        # 应只返回30条打卡记录
        assert len(profile_data["checkins"]) == 30

    @pytest.mark.asyncio
    async def test_get_profile_data_empty_user(self, db_session: AsyncSession):
        """测试获取空数据用户的主页数据"""
        user = await TestDataFactory.create_user(db_session)

        # 获取主页数据
        profile_data = await get_user_profile_data(
            db_session,
            user.id,
            user.id
        )

        assert profile_data["posts"] == []
        assert profile_data["checkins"] == []
        assert profile_data["follower_count"] == 0
        assert profile_data["following_count"] == 0


class TestListUsersForAdmin:
    """测试管理端用户列表"""

    @pytest.mark.asyncio
    async def test_list_users_default_pagination(self, db_session: AsyncSession):
        """测试默认分页参数"""
        # 创建25个用户
        for i in range(25):
            await TestDataFactory.create_user(
                db_session,
                anonymous_name=f"用户{i}"
            )

        # 使用默认分页参数查询
        users, total = await list_users_for_admin(db_session)

        assert total == 25
        assert len(users) == 20  # 默认limit=20

    @pytest.mark.asyncio
    async def test_list_users_with_custom_limit(self, db_session: AsyncSession):
        """测试自定义limit"""
        # 创建10个用户
        for i in range(10):
            await TestDataFactory.create_user(db_session)

        # 设置limit=5
        users, total = await list_users_for_admin(db_session, limit=5)

        assert total == 10
        assert len(users) == 5

    @pytest.mark.asyncio
    async def test_list_users_with_offset(self, db_session: AsyncSession):
        """测试偏移量"""
        # 创建10个用户
        for i in range(10):
            await TestDataFactory.create_user(
                db_session,
                anonymous_name=f"用户{i:02d}"
            )

        # 跳过前5条
        users, total = await list_users_for_admin(db_session, limit=10, offset=5)

        assert total == 10
        assert len(users) == 5

    @pytest.mark.asyncio
    async def test_list_users_ordered_by_created_at_desc(self, db_session: AsyncSession):
        """测试按创建时间倒序排列"""
        import time

        # 创建用户（间隔很短）
        user_ids = []
        for i in range(3):
            user = await TestDataFactory.create_user(db_session)
            user_ids.append(user.id)
            time.sleep(0.01)  # 确保创建时间不同

        # 查询用户列表
        users, total = await list_users_for_admin(db_session)

        assert total == 3
        assert len(users) == 3
        # 最后创建的用户应排在最前面
        assert users[0].id == user_ids[2]
        assert users[1].id == user_ids[1]
        assert users[2].id == user_ids[0]

    @pytest.mark.asyncio
    async def test_list_users_with_keyword_filter(self, db_session: AsyncSession):
        """测试按关键词筛选"""
        # 创建不同昵称的用户
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="快乐打工人"
        )
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="悲伤打工人"
        )
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="测试用户"
        )

        # 搜索关键词"打工人"
        users, total = await list_users_for_admin(db_session, keyword="打工人")

        assert total == 2
        assert len(users) == 2
        # 验证返回的用户包含关键词
        for user in users:
            assert "打工人" in user.anonymous_name

    @pytest.mark.asyncio
    async def test_list_users_with_keyword_whitespace(self, db_session: AsyncSession):
        """测试关键词包含空白字符时自动trim"""
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="打工人A"
        )
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="打工人B"
        )

        # 关键词带前后空格
        users, total = await list_users_for_admin(db_session, keyword="  打工人  ")

        assert total == 2
        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_list_users_with_status_filter(self, db_session: AsyncSession):
        """测试按状态筛选"""
        # 创建不同状态的用户
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="正常用户1",
            status="normal"
        )
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="正常用户2",
            status="normal"
        )
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="封禁用户",
            status="disabled"
        )

        # 筛选normal状态的用户
        users, total = await list_users_for_admin(db_session, status="normal")

        assert total == 2
        assert len(users) == 2
        for user in users:
            assert user.status == "normal"

    @pytest.mark.asyncio
    async def test_list_users_with_both_filters(self, db_session: AsyncSession):
        """测试同时使用关键词和状态筛选"""
        # 创建用户
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="活跃打工人A",
            status="normal"
        )
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="活跃打工人B",
            status="normal"
        )
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="打工人C",
            status="disabled"
        )
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="其他用户",
            status="normal"
        )

        # 同时筛选关键词"打工人"和状态"normal"
        users, total = await list_users_for_admin(
            db_session,
            keyword="打工人",
            status="normal"
        )

        assert total == 2
        assert len(users) == 2
        for user in users:
            assert "打工人" in user.anonymous_name
            assert user.status == "normal"

    @pytest.mark.asyncio
    async def test_list_users_empty_result(self, db_session: AsyncSession):
        """测试空结果集"""
        # 不创建任何用户

        users, total = await list_users_for_admin(db_session)

        assert total == 0
        assert len(users) == 0

    @pytest.mark.asyncio
    async def test_list_users_keyword_no_match(self, db_session: AsyncSession):
        """测试关键词无匹配结果"""
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="用户A"
        )

        # 搜索不存在的关键词
        users, total = await list_users_for_admin(db_session, keyword="不存在")

        assert total == 0
        assert len(users) == 0

    @pytest.mark.asyncio
    async def test_list_users_status_no_match(self, db_session: AsyncSession):
        """测试状态无匹配结果"""
        await TestDataFactory.create_user(
            db_session,
            anonymous_name="用户A",
            status="normal"
        )

        # 筛选不存在的状态
        users, total = await list_users_for_admin(db_session, status="deleted")

        assert total == 0
        assert len(users) == 0
