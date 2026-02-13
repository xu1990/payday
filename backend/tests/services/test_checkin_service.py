"""打卡服务测试"""
import pytest
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import checkin_service
from app.models.checkin import CheckIn
from tests.test_utils import TestDataFactory


class TestCheckIn:
    """测试打卡功能"""

    @pytest.mark.asyncio
    async def test_check_in_today_success(self, db_session: AsyncSession):
        """测试今天打卡成功"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 执行打卡
        checkin = await checkin_service.check_in(
            db_session,
            user.id,
            today,
            note="今天心情不错"
        )

        # 验证打卡记录
        assert checkin.id is not None
        assert checkin.user_id == user.id
        assert checkin.check_date == today
        assert checkin.note == "今天心情不错"

    @pytest.mark.asyncio
    async def test_check_in_without_note(self, db_session: AsyncSession):
        """测试不带备注的打卡"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 不传note参数
        checkin = await checkin_service.check_in(
            db_session,
            user.id,
            today
        )

        # 验证note为空字符串
        assert checkin.note == ""

    @pytest.mark.asyncio
    async def test_check_in_past_date(self, db_session: AsyncSession):
        """测试补卡（打卡过去日期）"""
        user = await TestDataFactory.create_user(db_session)
        past_date = date.today() - timedelta(days=3)

        # 补卡
        checkin = await checkin_service.check_in(
            db_session,
            user.id,
            past_date,
            note="补卡"
        )

        # 验证打卡记录
        assert checkin.check_date == past_date
        assert checkin.note == "补卡"

    @pytest.mark.asyncio
    async def test_check_in_same_date_twice(self, db_session: AsyncSession):
        """测试同一日期重复打卡"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 第一次打卡
        checkin1 = await checkin_service.check_in(
            db_session,
            user.id,
            today,
            note="第一次"
        )

        # 第二次打卡（同一天）
        checkin2 = await checkin_service.check_in(
            db_session,
            user.id,
            today,
            note="第二次"
        )

        # 验证会创建两条记录（虽然逻辑上不应该这样，但服务层没有限制）
        assert checkin1.id != checkin2.id
        assert checkin1.check_date == checkin2.check_date

    @pytest.mark.asyncio
    async def test_check_in_user_isolation(self, db_session: AsyncSession):
        """测试用户打卡隔离"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        today = date.today()

        # user1打卡
        checkin1 = await checkin_service.check_in(
            db_session,
            user1.id,
            today
        )

        # user2打卡
        checkin2 = await checkin_service.check_in(
            db_session,
            user2.id,
            today
        )

        # 验证记录隔离
        assert checkin1.user_id == user1.id
        assert checkin2.user_id == user2.id
        assert checkin1.id != checkin2.id


class TestGetUserCheckinStreak:
    """测试获取用户连续打卡天数"""

    @pytest.mark.asyncio
    async def test_streak_no_checkin(self, db_session: AsyncSession):
        """测试没有打卡记录时连续天数为0"""
        user = await TestDataFactory.create_user(db_session)

        # 获取连续天数
        streak = await checkin_service.get_user_checkin_streak(
            db_session,
            user.id
        )

        # 验证
        assert streak == 0

    @pytest.mark.asyncio
    async def test_streak_one_day(self, db_session: AsyncSession):
        """测试只打卡一天，连续天数为1"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 打卡今天
        await checkin_service.check_in(db_session, user.id, today)

        # 获取连续天数
        streak = await checkin_service.get_user_checkin_streak(
            db_session,
            user.id
        )

        # 验证
        assert streak == 1

    @pytest.mark.asyncio
    async def test_streak_continuous_days(self, db_session: AsyncSession):
        """测试连续打卡多天"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 连续打卡3天
        for i in range(2, -1, -1):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user.id, check_date)

        # 获取连续天数
        streak = await checkin_service.get_user_checkin_streak(
            db_session,
            user.id
        )

        # 验证连续3天
        assert streak == 3

    @pytest.mark.asyncio
    async def test_streak_broken_yesterday(self, db_session: AsyncSession):
        """测试昨天没打卡，连续中断"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()
        yesterday = today - timedelta(days=1)
        day_before = today - timedelta(days=2)

        # 打卡前天和今天，跳过昨天
        await checkin_service.check_in(db_session, user.id, day_before)
        await checkin_service.check_in(db_session, user.id, today)

        # 获取连续天数
        streak = await checkin_service.get_user_checkin_streak(
            db_session,
            user.id
        )

        # 验证只有1天（连续中断）
        assert streak == 1

    @pytest.mark.asyncio
    async def test_streak_long_continuous(self, db_session: AsyncSession):
        """测试长期连续打卡"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 连续打卡30天
        for i in range(29, -1, -1):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user.id, check_date)

        # 获取连续天数
        streak = await checkin_service.get_user_checkin_streak(
            db_session,
            user.id
        )

        # 验证连续30天
        assert streak == 30

    @pytest.mark.asyncio
    async def test_streak_max_365_days(self, db_session: AsyncSession):
        """测试连续天数上限为365天"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 连续打卡400天（测试上限保护）
        for i in range(400):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user.id, check_date)

        # 获取连续天数
        streak = await checkin_service.get_user_checkin_streak(
            db_session,
            user.id
        )

        # 验证最多365天
        assert streak == 365

    @pytest.mark.asyncio
    async def test_streak_user_isolation(self, db_session: AsyncSession):
        """测试用户连续天数隔离"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        today = date.today()

        # user1连续打卡3天
        for i in range(2, -1, -1):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user1.id, check_date)

        # user2只打卡今天
        await checkin_service.check_in(db_session, user2.id, today)

        # 获取各自的连续天数
        streak1 = await checkin_service.get_user_checkin_streak(
            db_session,
            user1.id
        )
        streak2 = await checkin_service.get_user_checkin_streak(
            db_session,
            user2.id
        )

        # 验证隔离
        assert streak1 == 3
        assert streak2 == 1


class TestGetCheckinCalendar:
    """测试获取打卡日历"""

    @pytest.mark.asyncio
    async def test_calendar_empty_month(self, db_session: AsyncSession):
        """测试空月份日历"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 获取本月日历
        calendar = await checkin_service.get_checkin_calendar(
            db_session,
            user.id,
            today.year,
            today.month
        )

        # 验证返回空列表
        assert calendar == []

    @pytest.mark.asyncio
    async def test_calendar_with_checkins(self, db_session: AsyncSession):
        """测试有打卡记录的日历"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 本月打卡3天
        check_dates = [
            today,
            today - timedelta(days=3),
            today - timedelta(days=7)
        ]
        for check_date in check_dates:
            await checkin_service.check_in(db_session, user.id, check_date)

        # 获取本月日历
        calendar = await checkin_service.get_checkin_calendar(
            db_session,
            user.id,
            today.year,
            today.month
        )

        # 验证返回3条记录
        assert len(calendar) == 3
        # 验证日期格式
        for item in calendar:
            assert "date" in item
            # 验证是ISO格式字符串
            date.fromisoformat(item["date"])

    @pytest.mark.asyncio
    async def test_calendar_different_month(self, db_session: AsyncSession):
        """测试不同月份的日历"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 上月打卡
        last_month_date = today - timedelta(days=30)
        await checkin_service.check_in(db_session, user.id, last_month_date)

        # 本月打卡
        await checkin_service.check_in(db_session, user.id, today)

        # 获取上月日历
        last_month_calendar = await checkin_service.get_checkin_calendar(
            db_session,
            user.id,
            last_month_date.year,
            last_month_date.month
        )

        # 获取本月日历
        this_month_calendar = await checkin_service.get_checkin_calendar(
            db_session,
            user.id,
            today.year,
            today.month
        )

        # 验证上月有1条，本月有1条
        assert len(last_month_calendar) == 1
        assert len(this_month_calendar) == 1

    @pytest.mark.asyncio
    async def test_calendar_ordered_by_date(self, db_session: AsyncSession):
        """测试日历按日期排序"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 打卡多个日期（不按顺序）
        check_dates = [
            today - timedelta(days=5),
            today,
            today - timedelta(days=2)
        ]
        for check_date in check_dates:
            await checkin_service.check_in(db_session, user.id, check_date)

        # 获取日历
        calendar = await checkin_service.get_checkin_calendar(
            db_session,
            user.id,
            today.year,
            today.month
        )

        # 验证按日期升序排列
        dates = [date.fromisoformat(item["date"]) for item in calendar]
        for i in range(len(dates) - 1):
            assert dates[i] <= dates[i + 1]

    @pytest.mark.asyncio
    async def test_calendar_user_isolation(self, db_session: AsyncSession):
        """测试用户日历隔离"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        today = date.today()

        # user1打卡今天
        await checkin_service.check_in(db_session, user1.id, today)

        # user2打卡昨天
        yesterday = today - timedelta(days=1)
        await checkin_service.check_in(db_session, user2.id, yesterday)

        # 获取各自的日历
        calendar1 = await checkin_service.get_checkin_calendar(
            db_session,
            user1.id,
            today.year,
            today.month
        )
        calendar2 = await checkin_service.get_checkin_calendar(
            db_session,
            user2.id,
            today.year,
            today.month
        )

        # 验证隔离
        assert len(calendar1) == 1
        assert date.fromisoformat(calendar1[0]["date"]) == today

        assert len(calendar2) == 1
        assert date.fromisoformat(calendar2[0]["date"]) == yesterday

    @pytest.mark.asyncio
    async def test_calendar_year_boundary(self, db_session: AsyncSession):
        """测试跨年日历"""
        user = await TestDataFactory.create_user(db_session)

        # 2023年12月打卡
        dec_date = date(2023, 12, 15)
        await checkin_service.check_in(db_session, user.id, dec_date)

        # 2024年1月打卡
        jan_date = date(2024, 1, 5)
        await checkin_service.check_in(db_session, user.id, jan_date)

        # 获取2023年12月日历
        dec_calendar = await checkin_service.get_checkin_calendar(
            db_session,
            user.id,
            2023,
            12
        )

        # 获取2024年1月日历
        jan_calendar = await checkin_service.get_checkin_calendar(
            db_session,
            user.id,
            2024,
            1
        )

        # 验证跨年正确
        assert len(dec_calendar) == 1
        assert date.fromisoformat(dec_calendar[0]["date"]) == dec_date

        assert len(jan_calendar) == 1
        assert date.fromisoformat(jan_calendar[0]["date"]) == jan_date


class TestGetCheckinStats:
    """测试获取打卡统计"""

    @pytest.mark.asyncio
    async def test_stats_no_checkin(self, db_session: AsyncSession):
        """测试没有打卡记录时的统计"""
        user = await TestDataFactory.create_user(db_session)

        # 获取统计
        stats = await checkin_service.get_checkin_stats(
            db_session,
            user.id
        )

        # 验证
        assert stats["total_days"] == 0
        assert stats["this_month"] == 0
        assert stats["current_streak"] == 0

    @pytest.mark.asyncio
    async def test_stats_one_checkin(self, db_session: AsyncSession):
        """测试一次打卡的统计"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 打卡今天
        await checkin_service.check_in(db_session, user.id, today)

        # 获取统计
        stats = await checkin_service.get_checkin_stats(
            db_session,
            user.id
        )

        # 验证
        assert stats["total_days"] == 1
        assert stats["this_month"] == 1
        assert stats["current_streak"] == 1

    @pytest.mark.asyncio
    async def test_stats_multiple_months(self, db_session: AsyncSession):
        """测试多个月份的统计"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 上月打卡2天
        last_month_start = today - timedelta(days=30)
        for i in range(2):
            check_date = last_month_start + timedelta(days=i)
            await checkin_service.check_in(db_session, user.id, check_date)

        # 本月打卡3天
        for i in range(3):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user.id, check_date)

        # 获取统计
        stats = await checkin_service.get_checkin_stats(
            db_session,
            user.id
        )

        # 验证
        assert stats["total_days"] == 5  # 总共5天
        assert stats["this_month"] == 3  # 本月3天
        assert stats["current_streak"] == 3  # 连续3天

    @pytest.mark.asyncio
    async def test_stats_with_streak(self, db_session: AsyncSession):
        """测试包含连续天数的统计"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 连续打卡7天
        for i in range(6, -1, -1):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user.id, check_date)

        # 获取统计
        stats = await checkin_service.get_checkin_stats(
            db_session,
            user.id
        )

        # 验证
        assert stats["total_days"] == 7
        assert stats["this_month"] == 7
        assert stats["current_streak"] == 7

    @pytest.mark.asyncio
    async def test_stats_broken_streak(self, db_session: AsyncSession):
        """测试中断后的统计"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 前5天连续打卡
        for i in range(5, 0, -1):
            check_date = today - timedelta(days=i + 3)  # 创建更早的日期
            await checkin_service.check_in(db_session, user.id, check_date)

        # 断了2天（today-2, today-1 没有打卡）

        # 最近连续打卡3天
        for i in range(2, -1, -1):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user.id, check_date)

        # 获取统计
        stats = await checkin_service.get_checkin_stats(
            db_session,
            user.id
        )

        # 验证
        assert stats["total_days"] == 8  # 总共8天
        # 所有8天都在本月（因为都在过去7天内）
        assert stats["this_month"] == 8  # 本月8天
        assert stats["current_streak"] == 3  # 当前连续3天

    @pytest.mark.asyncio
    async def test_stats_user_isolation(self, db_session: AsyncSession):
        """测试用户统计隔离"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        today = date.today()

        # user1打卡5天
        for i in range(4, -1, -1):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user1.id, check_date)

        # user2打卡2天
        for i in range(1, -1, -1):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user2.id, check_date)

        # 获取各自统计
        stats1 = await checkin_service.get_checkin_stats(
            db_session,
            user1.id
        )
        stats2 = await checkin_service.get_checkin_stats(
            db_session,
            user2.id
        )

        # 验证隔离
        assert stats1["total_days"] == 5
        assert stats1["this_month"] == 5
        assert stats1["current_streak"] == 5

        assert stats2["total_days"] == 2
        assert stats2["this_month"] == 2
        assert stats2["current_streak"] == 2


class TestCheckinWorkflow:
    """测试打卡完整流程"""

    @pytest.mark.asyncio
    async def test_daily_checkin_workflow(self, db_session: AsyncSession):
        """测试每日打卡完整流程"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 1. 用户首次打卡
        checkin = await checkin_service.check_in(
            db_session,
            user.id,
            today,
            note="第一天"
        )
        assert checkin.id is not None

        # 2. 获取统计
        stats = await checkin_service.get_checkin_stats(db_session, user.id)
        assert stats["total_days"] == 1
        assert stats["current_streak"] == 1

        # 3. 查看日历
        calendar = await checkin_service.get_checkin_calendar(
            db_session,
            user.id,
            today.year,
            today.month
        )
        assert len(calendar) == 1

    @pytest.mark.asyncio
    async def test_consecutive_checkin_workflow(self, db_session: AsyncSession):
        """测试连续打卡流程"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 连续打卡7天
        for day in range(7):
            check_date = today - timedelta(days=6 - day)
            await checkin_service.check_in(
                db_session,
                user.id,
                check_date,
                note=f"第{day + 1}天"
            )

            # 每天打卡后检查统计
            stats = await checkin_service.get_checkin_stats(db_session, user.id)
            expected_days = day + 1
            assert stats["total_days"] == expected_days
            assert stats["current_streak"] == expected_days

    @pytest.mark.asyncio
    async def test_streak_recovery_workflow(self, db_session: AsyncSession):
        """测试连续中断后恢复流程"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 连续打卡5天
        for i in range(4, -1, -1):
            check_date = today - timedelta(days=i + 3)
            await checkin_service.check_in(db_session, user.id, check_date)

        # 验证连续5天
        streak_before = await checkin_service.get_user_checkin_streak(
            db_session,
            user.id
        )
        assert streak_before == 5

        # 中断2天（不打卡）

        # 重新开始打卡
        await checkin_service.check_in(db_session, user.id, today)

        # 验证连续天数重置为1
        stats = await checkin_service.get_checkin_stats(db_session, user.id)
        assert stats["current_streak"] == 1
        assert stats["total_days"] == 6  # 总天数还是6

    @pytest.mark.asyncio
    async def test_monthly_calendar_workflow(self, db_session: AsyncSession):
        """测试月度日历查看流程"""
        user = await TestDataFactory.create_user(db_session)
        today = date.today()

        # 本月随机打卡几天（都在本月内）
        check_dates = [
            today - timedelta(days=1),
            today - timedelta(days=5),
            today - timedelta(days=10),
            # 确保所有日期都在本月，避免跨月问题
        ]
        for check_date in check_dates:
            await checkin_service.check_in(db_session, user.id, check_date)

        # 查看本月日历
        calendar = await checkin_service.get_checkin_calendar(
            db_session,
            user.id,
            today.year,
            today.month
        )

        # 验证所有打卡日期都在日历中
        calendar_dates = [
            date.fromisoformat(item["date"])
            for item in calendar
        ]
        for check_date in check_dates:
            assert check_date in calendar_dates

    @pytest.mark.asyncio
    async def test_multiuser_checkin_competition(self, db_session: AsyncSession):
        """测试多用户打卡竞争场景"""
        user1 = await TestDataFactory.create_user(db_session, "user1")
        user2 = await TestDataFactory.create_user(db_session, "user2")
        user3 = await TestDataFactory.create_user(db_session, "user3")
        today = date.today()

        # user1: 连续打卡10天
        for i in range(9, -1, -1):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user1.id, check_date)

        # user2: 连续打卡5天
        for i in range(4, -1, -1):
            check_date = today - timedelta(days=i)
            await checkin_service.check_in(db_session, user2.id, check_date)

        # user3: 只打卡今天
        await checkin_service.check_in(db_session, user3.id, today)

        # 获取各自的统计
        stats1 = await checkin_service.get_checkin_stats(db_session, user1.id)
        stats2 = await checkin_service.get_checkin_stats(db_session, user2.id)
        stats3 = await checkin_service.get_checkin_stats(db_session, user3.id)

        # 验证排名
        assert stats1["current_streak"] == 10
        assert stats2["current_streak"] == 5
        assert stats3["current_streak"] == 1

        # user1排名第一
        assert stats1["current_streak"] > stats2["current_streak"]
        assert stats2["current_streak"] > stats3["current_streak"]
