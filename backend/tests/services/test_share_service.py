"""分享服务测试"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.share_service import (
    create_share,
    update_share_status,
    get_user_shares,
    get_share_stats,
)
from app.models.share import Share
from app.core.exceptions import NotFoundException


class TestCreateShare:
    """测试创建分享记录"""

    @pytest.mark.asyncio
    async def test_create_share_success(self, db_session: AsyncSession):
        """测试成功创建分享记录"""
        user_id = "test_user_123"

        share = await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_456",
            share_channel="wechat_friend",
        )

        assert share.id is not None
        assert share.user_id == user_id
        assert share.target_type == "post"
        assert share.target_id == "post_456"
        assert share.share_channel == "wechat_friend"
        assert share.share_status == "pending"

    @pytest.mark.asyncio
    async def test_create_share_different_target_types(self, db_session: AsyncSession):
        """测试创建不同类型的分享记录"""
        user_id = "test_user_123"

        # 分享帖子
        post_share = await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_123",
            share_channel="wechat_friend",
        )
        assert post_share.target_type == "post"

        # 分享工资
        salary_share = await create_share(
            db_session,
            user_id=user_id,
            target_type="salary",
            target_id="salary_456",
            share_channel="wechat_moments",
        )
        assert salary_share.target_type == "salary"

        # 分享海报
        poster_share = await create_share(
            db_session,
            user_id=user_id,
            target_type="poster",
            target_id="poster_789",
            share_channel="wechat_friend",
        )
        assert poster_share.target_type == "poster"

    @pytest.mark.asyncio
    async def test_create_share_different_channels(self, db_session: AsyncSession):
        """测试不同分享渠道"""
        user_id = "test_user_123"

        # 分享到微信好友
        friend_share = await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_123",
            share_channel="wechat_friend",
        )
        assert friend_share.share_channel == "wechat_friend"

        # 分享到朋友圈
        moments_share = await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_123",
            share_channel="wechat_moments",
        )
        assert moments_share.share_channel == "wechat_moments"


class TestUpdateShareStatus:
    """测试更新分享状态"""

    @pytest.mark.asyncio
    async def test_update_status_to_success(self, db_session: AsyncSession):
        """测试更新状态为成功"""
        # 先创建分享记录
        share = await create_share(
            db_session,
            user_id="user_123",
            target_type="post",
            target_id="post_456",
            share_channel="wechat_friend",
        )

        # 更新为成功
        updated_share = await update_share_status(
            db_session,
            share_id=share.id,
            status="success",
        )

        assert updated_share.share_status == "success"
        assert updated_share.id == share.id

    @pytest.mark.asyncio
    async def test_update_status_to_failed_with_error(self, db_session: AsyncSession):
        """测试更新状态为失败并记录错误信息"""
        share = await create_share(
            db_session,
            user_id="user_123",
            target_type="post",
            target_id="post_456",
            share_channel="wechat_friend",
        )

        # 更新为失败
        updated_share = await update_share_status(
            db_session,
            share_id=share.id,
            status="failed",
            error_message="用户取消分享",
        )

        assert updated_share.share_status == "failed"
        # Note: error_message field may need to be added to Share model

    @pytest.mark.asyncio
    async def test_update_status_without_error_message(self, db_session: AsyncSession):
        """测试更新失败状态但不提供错误信息"""
        share = await create_share(
            db_session,
            user_id="user_123",
            target_type="post",
            target_id="post_456",
            share_channel="wechat_friend",
        )

        # 更新为失败但不提供错误信息
        updated_share = await update_share_status(
            db_session,
            share_id=share.id,
            status="failed",
        )

        assert updated_share.share_status == "failed"

    @pytest.mark.asyncio
    async def test_update_nonexistent_share_raises_exception(self, db_session: AsyncSession):
        """测试更新不存在的分享记录抛出异常"""
        with pytest.raises(NotFoundException) as exc_info:
            await update_share_status(
                db_session,
                share_id="nonexistent_share_id",
                status="success",
            )

        assert "不存在" in str(exc_info.value)


class TestGetUserShares:
    """测试获取用户分享记录"""

    @pytest.mark.asyncio
    async def test_get_shares_without_filter(self, db_session: AsyncSession):
        """测试获取用户所有分享记录"""
        user_id = "user_123"

        # 创建多个分享记录
        await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )
        await create_share(
            db_session,
            user_id=user_id,
            target_type="salary",
            target_id="salary_1",
            share_channel="wechat_moments",
        )

        shares, total = await get_user_shares(db_session, user_id)

        assert total == 2
        assert len(shares) == 2

    @pytest.mark.asyncio
    async def test_get_shares_with_target_type_filter(self, db_session: AsyncSession):
        """测试按目标类型筛选"""
        user_id = "user_123"

        # 创建不同类型的分享
        await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )
        await create_share(
            db_session,
            user_id=user_id,
            target_type="salary",
            target_id="salary_1",
            share_channel="wechat_moments",
        )
        await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_2",
            share_channel="wechat_friend",
        )

        # 只获取post类型
        shares, total = await get_user_shares(
            db_session,
            user_id,
            target_type="post",
        )

        assert total == 2
        assert len(shares) == 2
        assert all(s.target_type == "post" for s in shares)

    @pytest.mark.asyncio
    async def test_get_shares_ordered_by_created_at_desc(self, db_session: AsyncSession):
        """测试按创建时间倒序排列"""
        import time

        user_id = "user_123"

        # 创建多个分享记录
        share1 = await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )
        time.sleep(0.01)  # 确保时间不同
        share2 = await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_2",
            share_channel="wechat_moments",
        )

        shares, total = await get_user_shares(db_session, user_id)

        # 最后创建的应排在前面
        assert shares[0].id == share2.id
        assert shares[1].id == share1.id

    @pytest.mark.asyncio
    async def test_get_shares_with_pagination(self, db_session: AsyncSession):
        """测试分页功能"""
        user_id = "user_123"

        # 创建5条记录
        for i in range(5):
            await create_share(
                db_session,
                user_id=user_id,
                target_type="post",
                target_id=f"post_{i}",
                share_channel="wechat_friend",
            )

        # 第一页：2条
        shares1, total1 = await get_user_shares(
            db_session,
            user_id,
            limit=2,
            offset=0,
        )
        assert total1 == 5
        assert len(shares1) == 2

        # 第二页：2条
        shares2, total2 = await get_user_shares(
            db_session,
            user_id,
            limit=2,
            offset=2,
        )
        assert total2 == 5
        assert len(shares2) == 2

        # 第三页：1条
        shares3, total3 = await get_user_shares(
            db_session,
            user_id,
            limit=2,
            offset=4,
        )
        assert total3 == 5
        assert len(shares3) == 1

    @pytest.mark.asyncio
    async def test_get_shares_empty_result(self, db_session: AsyncSession):
        """测试空结果"""
        shares, total = await get_user_shares(db_session, "nonexistent_user")

        assert total == 0
        assert shares == []

    @pytest.mark.asyncio
    async def test_get_shares_only_current_users(self, db_session: AsyncSession):
        """测试只获取当前用户的分享记录"""
        user1 = "user_123"
        user2 = "user_456"

        # 为两个用户创建分享记录
        await create_share(
            db_session,
            user_id=user1,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )
        await create_share(
            db_session,
            user_id=user2,
            target_type="post",
            target_id="post_2",
            share_channel="wechat_moments",
        )

        # 只获取user1的记录
        shares, total = await get_user_shares(db_session, user1)

        assert total == 1
        assert len(shares) == 1
        assert shares[0].user_id == user1


class TestGetShareStats:
    """测试获取分享统计"""

    @pytest.mark.asyncio
    async def test_get_stats_default_7_days(self, db_session: AsyncSession):
        """测试获取默认7天的统计"""
        user_id = "user_123"

        # 创建最近的分享记录
        await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )
        # 标记为成功
        share = await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_2",
            share_channel="wechat_moments",
        )
        await update_share_status(db_session, share.id, "success")

        stats = await get_share_stats(db_session, user_id)

        assert stats["total_shares"] == 2
        assert stats["success_shares"] == 1
        assert stats["success_rate"] == "50.0%"
        assert stats["days"] == 7

    @pytest.mark.asyncio
    async def test_get_stats_custom_days(self, db_session: AsyncSession):
        """测试自定义统计天数"""
        user_id = "user_123"

        # 创建分享记录
        await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )

        # 统计30天
        stats_30 = await get_share_stats(db_session, user_id, days=30)
        assert stats_30["days"] == 30
        assert stats_30["total_shares"] == 1

        # 统计1天
        stats_1 = await get_share_stats(db_session, user_id, days=1)
        assert stats_1["days"] == 1
        assert stats_1["total_shares"] == 1

    @pytest.mark.asyncio
    async def test_get_stats_only_recent(self, db_session: AsyncSession):
        """测试只统计最近N天的记录"""
        user_id = "user_123"

        # 创建一个分享记录（在统计范围内）
        await create_share(
            db_session,
            user_id=user_id,
            target_type="post",
            target_id="post_1",
            share_channel="wechat_friend",
        )

        # 统计1天
        stats = await get_share_stats(db_session, user_id, days=1)
        assert stats["total_shares"] == 1

    @pytest.mark.asyncio
    async def test_get_stats_zero_shares(self, db_session: AsyncSession):
        """测试没有分享记录时的统计"""
        stats = await get_share_stats(db_session, "nonexistent_user", days=7)

        assert stats["total_shares"] == 0
        assert stats["success_shares"] == 0
        assert stats["success_rate"] == "0.0%"
        assert stats["days"] == 7

    @pytest.mark.asyncio
    async def test_get_stats_all_success(self, db_session: AsyncSession):
        """测试所有分享都成功"""
        user_id = "user_123"

        # 创建3个分享记录并标记为成功
        for i in range(3):
            share = await create_share(
                db_session,
                user_id=user_id,
                target_type="post",
                target_id=f"post_{i}",
                share_channel="wechat_friend",
            )
            await update_share_status(db_session, share.id, "success")

        stats = await get_share_stats(db_session, user_id, days=7)

        assert stats["total_shares"] == 3
        assert stats["success_shares"] == 3
        assert stats["success_rate"] == "100.0%"

    @pytest.mark.asyncio
    async def test_get_stats_all_failed(self, db_session: AsyncSession):
        """测试所有分享都失败"""
        user_id = "user_123"

        # 创建3个分享记录并标记为失败
        for i in range(3):
            share = await create_share(
                db_session,
                user_id=user_id,
                target_type="post",
                target_id=f"post_{i}",
                share_channel="wechat_friend",
            )
            await update_share_status(db_session, share.id, "failed")

        stats = await get_share_stats(db_session, user_id, days=7)

        assert stats["total_shares"] == 3
        assert stats["success_shares"] == 0
        assert stats["success_rate"] == "0.0%"

    @pytest.mark.asyncio
    async def test_get_stats_mixed_status(self, db_session: AsyncSession):
        """测试混合状态的成功率计算"""
        user_id = "user_123"

        # 创建4个分享记录：2成功，1失败，1待处理
        shares = []
        for i in range(4):
            share = await create_share(
                db_session,
                user_id=user_id,
                target_type="post",
                target_id=f"post_{i}",
                share_channel="wechat_friend",
            )
            shares.append(share)

        await update_share_status(db_session, shares[0].id, "success")
        await update_share_status(db_session, shares[1].id, "success")
        await update_share_status(db_session, shares[2].id, "failed")
        # shares[3] 保持 pending 状态

        stats = await get_share_stats(db_session, user_id, days=7)

        assert stats["total_shares"] == 4
        assert stats["success_shares"] == 2
        assert stats["success_rate"] == "50.0%"
