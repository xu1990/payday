"""统计服务集成测试"""
import pytest
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.statistics_service import (
    get_month_summary,
    get_trend,
    get_admin_dashboard_stats,
    get_insights_distributions,
)
from tests.test_utils import TestDataFactory


class TestGetMonthSummary:
    """测试获取月度汇总"""

    @pytest.mark.asyncio
    async def test_get_month_summary_empty(self, db_session: AsyncSession):
        """测试空月份汇总"""
        user = await TestDataFactory.create_user(db_session)

        summary = await get_month_summary(db_session, user.id, 2024, 1)

        assert summary["year"] == 2024
        assert summary["month"] == 1
        assert summary["total_amount"] == 0
        assert summary["record_count"] == 0

    @pytest.mark.asyncio
    async def test_get_month_summary_single_record(self, db_session: AsyncSession):
        """测试单条记录的月度汇总"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建1月的工资记录
        await TestDataFactory.create_salary(
            db_session,
            user.id,
            config.id,
            amount=15000.00,
            payday_date=date(2024, 1, 15)
        )

        summary = await get_month_summary(db_session, user.id, 2024, 1)

        assert summary["year"] == 2024
        assert summary["month"] == 1
        assert summary["total_amount"] == 15000.00
        assert summary["record_count"] == 1

    @pytest.mark.asyncio
    async def test_get_month_summary_multiple_records(self, db_session: AsyncSession):
        """测试多条记录的月度汇总"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建多条1月的工资记录
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=10000.00,
            payday_date=date(2024, 1, 15)
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=5000.00,
            payday_date=date(2024, 1, 20)
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=2000.50,
            payday_date=date(2024, 1, 25)
        )

        summary = await get_month_summary(db_session, user.id, 2024, 1)

        assert summary["year"] == 2024
        assert summary["month"] == 1
        assert summary["total_amount"] == 17000.50
        assert summary["record_count"] == 3

    @pytest.mark.asyncio
    async def test_get_month_summary_filters_by_month(self, db_session: AsyncSession):
        """测试按月份筛选"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建不同月份的记录
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=10000.00,
            payday_date=date(2024, 1, 15)
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=15000.00,
            payday_date=date(2024, 2, 15)
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=20000.00,
            payday_date=date(2024, 3, 15)
        )

        # 获取1月汇总
        jan_summary = await get_month_summary(db_session, user.id, 2024, 1)
        assert jan_summary["total_amount"] == 10000.00
        assert jan_summary["record_count"] == 1

        # 获取2月汇总
        feb_summary = await get_month_summary(db_session, user.id, 2024, 2)
        assert feb_summary["total_amount"] == 15000.00
        assert feb_summary["record_count"] == 1

    @pytest.mark.asyncio
    async def test_get_month_summary_december(self, db_session: AsyncSession):
        """测试12月份的汇总"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建12月的工资记录
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=18000.00,
            payday_date=date(2024, 12, 25)
        )

        summary = await get_month_summary(db_session, user.id, 2024, 12)

        assert summary["year"] == 2024
        assert summary["month"] == 12
        assert summary["total_amount"] == 18000.00
        assert summary["record_count"] == 1

    @pytest.mark.asyncio
    async def test_get_month_summary_user_isolation(self, db_session: AsyncSession):
        """测试用户数据隔离"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        # 创建 payday configs
        from app.models.payday import PaydayConfig
        config1 = PaydayConfig(user_id=user1.id, job_name="工作1", payday=25)
        config2 = PaydayConfig(user_id=user2.id, job_name="工作2", payday=15)
        db_session.add(config1)
        db_session.add(config2)
        await db_session.commit()
        await db_session.refresh(config1)
        await db_session.refresh(config2)

        # 为两个用户创建1月的记录
        await TestDataFactory.create_salary(
            db_session, user1.id, config1.id,
            amount=10000.00,
            payday_date=date(2024, 1, 15)
        )
        await TestDataFactory.create_salary(
            db_session, user2.id, config2.id,
            amount=20000.00,
            payday_date=date(2024, 1, 15)
        )

        # user1 的汇总
        summary1 = await get_month_summary(db_session, user1.id, 2024, 1)
        assert summary1["total_amount"] == 10000.00
        assert summary1["record_count"] == 1

        # user2 的汇总
        summary2 = await get_month_summary(db_session, user2.id, 2024, 1)
        assert summary2["total_amount"] == 20000.00
        assert summary2["record_count"] == 1


class TestGetTrend:
    """测试获取趋势数据"""

    @pytest.mark.asyncio
    async def test_get_trend_default_six_months(self, db_session: AsyncSession):
        """测试默认获取6个月趋势"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        trend = await get_trend(db_session, user.id)

        assert len(trend) == 6
        # 验证返回的是最近的6个月
        assert all("year" in t for t in trend)
        assert all("month" in t for t in trend)
        assert all("total_amount" in t for t in trend)
        assert all("record_count" in t for t in trend)

    @pytest.mark.asyncio
    async def test_get_trend_custom_months(self, db_session: AsyncSession):
        """测试自定义月份数"""
        user = await TestDataFactory.create_user(db_session)

        # 测试3个月
        trend_3 = await get_trend(db_session, user.id, months=3)
        assert len(trend_3) == 3

        # 测试12个月
        trend_12 = await get_trend(db_session, user.id, months=12)
        assert len(trend_12) == 12

    @pytest.mark.asyncio
    async def test_get_trend_with_data(self, db_session: AsyncSession):
        """测试包含数据的趋势"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建最近几个月的工资记录
        today = date.today()
        for i in range(3):
            # 计算月份
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1

            await TestDataFactory.create_salary(
                db_session, user.id, config.id,
                amount=10000.00 + i * 1000,
                payday_date=date(y, m, 15)
            )

        trend = await get_trend(db_session, user.id, months=3)

        # 验证趋势数据
        assert len(trend) == 3
        # 至少有一个月有数据
        has_data = any(t["record_count"] > 0 for t in trend)
        assert has_data

    @pytest.mark.asyncio
    async def test_get_trend_year_boundary(self, db_session: AsyncSession):
        """测试跨年边界"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建去年12月的记录
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=15000.00,
            payday_date=date(2023, 12, 15)
        )

        # 获取趋势（包含去年12月）
        trend = await get_trend(db_session, user.id, months=3)

        # 验证返回3个月的数据
        assert len(trend) == 3
        # 验证所有数据都有正确的字段
        assert all("year" in t for t in trend)
        assert all("month" in t for t in trend)
        assert all("total_amount" in t for t in trend)
        assert all("record_count" in t for t in trend)


class TestGetAdminDashboardStats:
    """测试管理端仪表盘统计"""

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_stats_empty(self, db_session: AsyncSession):
        """测试空数据库的统计"""
        stats = await get_admin_dashboard_stats(db_session)

        assert stats["user_total"] == 0
        assert stats["user_new_today"] == 0
        assert stats["salary_record_total"] == 0
        assert stats["salary_record_today"] == 0

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_stats_with_users(self, db_session: AsyncSession):
        """测试用户统计"""
        # 创建几个用户
        await TestDataFactory.create_user(db_session)
        await TestDataFactory.create_user(db_session)
        await TestDataFactory.create_user(db_session)

        stats = await get_admin_dashboard_stats(db_session)

        assert stats["user_total"] == 3

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_stats_today_users(self, db_session: AsyncSession):
        """测试今日新增用户统计"""
        # 由于测试使用的是 datetime.utcnow，创建的用户都会是今日的
        await TestDataFactory.create_user(db_session)
        await TestDataFactory.create_user(db_session)

        stats = await get_admin_dashboard_stats(db_session)

        assert stats["user_new_today"] == 2

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_stats_with_salaries(self, db_session: AsyncSession):
        """测试工资记录统计"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建工资记录
        await TestDataFactory.create_salary(db_session, user.id, config.id)
        await TestDataFactory.create_salary(db_session, user.id, config.id)
        await TestDataFactory.create_salary(db_session, user.id, config.id)

        stats = await get_admin_dashboard_stats(db_session)

        assert stats["salary_record_total"] == 3

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_stats_today_salaries(self, db_session: AsyncSession):
        """测试今日新增工资记录统计"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建今日的工资记录
        await TestDataFactory.create_salary(db_session, user.id, config.id)
        await TestDataFactory.create_salary(db_session, user.id, config.id)

        stats = await get_admin_dashboard_stats(db_session)

        assert stats["salary_record_today"] == 2

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_stats_comprehensive(self, db_session: AsyncSession):
        """测试综合统计"""
        # 创建用户
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        # 创建 payday configs
        from app.models.payday import PaydayConfig
        config1 = PaydayConfig(user_id=user1.id, job_name="工作1", payday=25)
        config2 = PaydayConfig(user_id=user2.id, job_name="工作2", payday=15)
        db_session.add(config1)
        db_session.add(config2)
        await db_session.commit()
        await db_session.refresh(config1)
        await db_session.refresh(config2)

        # 创建工资记录
        await TestDataFactory.create_salary(db_session, user1.id, config1.id)
        await TestDataFactory.create_salary(db_session, user2.id, config2.id)
        await TestDataFactory.create_salary(db_session, user2.id, config2.id)

        stats = await get_admin_dashboard_stats(db_session)

        assert stats["user_total"] == 2
        assert stats["user_new_today"] == 2  # 所有用户都是今天创建的
        assert stats["salary_record_total"] == 3
        assert stats["salary_record_today"] == 3  # 所有记录都是今天创建的


class TestGetInsightsDistributions:
    """测试数据洞察分布"""

    @pytest.mark.asyncio
    async def test_get_insights_distributions_empty(self, db_session: AsyncSession):
        """测试空数据库的分布"""
        insights = await get_insights_distributions(db_session)

        assert "industry_distribution" in insights
        assert "city_distribution" in insights
        assert "salary_range_distribution" in insights
        assert "payday_distribution" in insights
        assert "total_posts" in insights

        assert insights["industry_distribution"]["total"] == 0
        assert insights["industry_distribution"]["data"] == []

        assert insights["city_distribution"]["total"] == 0
        assert insights["city_distribution"]["data"] == []

        assert insights["salary_range_distribution"]["total"] == 0
        # 工资区间始终返回所有区间，即使数量为0
        assert len(insights["salary_range_distribution"]["data"]) == 6

        assert insights["payday_distribution"]["total"] == 0
        assert insights["payday_distribution"]["data"] == []

        assert insights["total_posts"] == 0

    @pytest.mark.asyncio
    async def test_insights_industry_distribution(self, db_session: AsyncSession):
        """测试行业分布"""
        user = await TestDataFactory.create_user(db_session)

        # 创建不同行业的帖子
        await TestDataFactory.create_post(
            db_session, user.id,
            industry="互联网",
            risk_status="approved",
            status="normal"
        )
        await TestDataFactory.create_post(
            db_session, user.id,
            industry="互联网",
            risk_status="approved",
            status="normal"
        )
        await TestDataFactory.create_post(
            db_session, user.id,
            industry="金融",
            risk_status="approved",
            status="normal"
        )

        insights = await get_insights_distributions(db_session)

        industry_dist = insights["industry_distribution"]
        assert industry_dist["total"] == 2  # 两个不同的行业
        assert len(industry_dist["data"]) == 2

        # 验证数据
        industries = {item["label"]: item["value"] for item in industry_dist["data"]}
        assert industries["互联网"] == 2
        assert industries["金融"] == 1

    @pytest.mark.asyncio
    async def test_insights_industry_distribution_top_10(self, db_session: AsyncSession):
        """测试行业分布Top 10"""
        user = await TestDataFactory.create_user(db_session)

        # 创建15个不同行业的帖子
        industries = [f"行业{i}" for i in range(15)]
        for industry in industries:
            await TestDataFactory.create_post(
                db_session, user.id,
                industry=industry,
                risk_status="approved",
                status="normal"
            )

        insights = await get_insights_distributions(db_session)

        industry_dist = insights["industry_distribution"]
        # 应该只返回Top 10
        assert industry_dist["total"] <= 10
        assert len(industry_dist["data"]) <= 10

    @pytest.mark.asyncio
    async def test_insights_city_distribution(self, db_session: AsyncSession):
        """测试城市分布"""
        user = await TestDataFactory.create_user(db_session)

        # 创建不同城市的帖子
        await TestDataFactory.create_post(
            db_session, user.id,
            city="北京",
            risk_status="approved",
            status="normal"
        )
        await TestDataFactory.create_post(
            db_session, user.id,
            city="北京",
            risk_status="approved",
            status="normal"
        )
        await TestDataFactory.create_post(
            db_session, user.id,
            city="上海",
            risk_status="approved",
            status="normal"
        )

        insights = await get_insights_distributions(db_session)

        city_dist = insights["city_distribution"]
        assert city_dist["total"] == 2  # 两个不同的城市
        assert len(city_dist["data"]) == 2

        # 验证数据
        cities = {item["label"]: item["value"] for item in city_dist["data"]}
        assert cities["北京"] == 2
        assert cities["上海"] == 1

    @pytest.mark.asyncio
    async def test_insights_salary_range_distribution(self, db_session: AsyncSession):
        """测试工资区间分布"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建不同工资范围的记录
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=2500.00  # 0-3K
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=4000.00  # 3-5K
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=8000.00  # 5-10K
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=12000.00  # 10-15K
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=18000.00  # 15-20K
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=25000.00  # 20K+
        )

        insights = await get_insights_distributions(db_session)

        salary_dist = insights["salary_range_distribution"]
        assert salary_dist["total"] == 6
        assert len(salary_dist["data"]) == 6

        # 验证每个区间都有数据
        ranges = {item["label"]: item["value"] for item in salary_dist["data"]}
        assert ranges["0-3K"] == 1
        assert ranges["3-5K"] == 1
        assert ranges["5-10K"] == 1
        assert ranges["10-15K"] == 1
        assert ranges["15-20K"] == 1
        assert ranges["20K+"] == 1

    @pytest.mark.asyncio
    async def test_insights_salary_range_boundary_values(self, db_session: AsyncSession):
        """测试工资区间边界值"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 测试边界值
        await TestDataFactory.create_salary(db_session, user.id, config.id, amount=2999.99)  # 0-3K
        await TestDataFactory.create_salary(db_session, user.id, config.id, amount=3000.00)  # 3-5K
        await TestDataFactory.create_salary(db_session, user.id, config.id, amount=5000.00)  # 5-10K
        await TestDataFactory.create_salary(db_session, user.id, config.id, amount=10000.00)  # 10-15K
        await TestDataFactory.create_salary(db_session, user.id, config.id, amount=15000.00)  # 15-20K
        await TestDataFactory.create_salary(db_session, user.id, config.id, amount=20000.00)  # 20K+

        insights = await get_insights_distributions(db_session)

        ranges = {item["label"]: item["value"] for item in insights["salary_range_distribution"]["data"]}
        assert ranges["0-3K"] == 1
        assert ranges["3-5K"] == 1
        assert ranges["5-10K"] == 1
        assert ranges["10-15K"] == 1
        assert ranges["15-20K"] == 1
        assert ranges["20K+"] == 1

    @pytest.mark.asyncio
    async def test_insights_payday_distribution(self, db_session: AsyncSession):
        """测试发薪日分布"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        # 创建不同发薪日的配置
        from app.models.payday import PaydayConfig
        config1 = PaydayConfig(user_id=user1.id, job_name="工作1", payday=10, calendar_type="solar")
        config2 = PaydayConfig(user_id=user2.id, job_name="工作2", payday=25, calendar_type="solar")
        config3 = PaydayConfig(user_id=user1.id, job_name="工作3", payday=25, calendar_type="solar")
        db_session.add(config1)
        db_session.add(config2)
        db_session.add(config3)
        await db_session.commit()

        insights = await get_insights_distributions(db_session)

        payday_dist = insights["payday_distribution"]
        # 应该有两个不同的发薪日
        assert payday_dist["total"] == 2

        # 验证数据
        paydays = {item["label"]: item["value"] for item in payday_dist["data"]}
        assert paydays.get("10号") == 1
        assert paydays.get("25号") == 2

    @pytest.mark.asyncio
    async def test_insights_only_approved_posts(self, db_session: AsyncSession):
        """测试只统计审核通过的帖子"""
        user = await TestDataFactory.create_user(db_session)

        # 创建不同状态的帖子
        await TestDataFactory.create_post(
            db_session, user.id,
            industry="互联网",
            risk_status="approved",
            status="normal"
        )
        await TestDataFactory.create_post(
            db_session, user.id,
            industry="金融",
            risk_status="pending",
            status="normal"
        )
        await TestDataFactory.create_post(
            db_session, user.id,
            industry="教育",
            risk_status="rejected",
            status="normal"
        )

        insights = await get_insights_distributions(db_session)

        # 只应该统计审核通过的帖子
        assert insights["total_posts"] == 1
        industry_dist = insights["industry_distribution"]
        assert len(industry_dist["data"]) == 1
        assert industry_dist["data"][0]["label"] == "互联网"

    @pytest.mark.asyncio
    async def test_insights_normal_status_only(self, db_session: AsyncSession):
        """测试只统计正常状态的帖子"""
        user = await TestDataFactory.create_user(db_session)

        # 创建不同状态的帖子
        await TestDataFactory.create_post(
            db_session, user.id,
            industry="互联网",
            risk_status="approved",
            status="normal"
        )
        await TestDataFactory.create_post(
            db_session, user.id,
            industry="金融",
            risk_status="approved",
            status="deleted"
        )

        insights = await get_insights_distributions(db_session)

        # 只应该统计正常状态的帖子
        assert insights["total_posts"] == 1
        industry_dist = insights["industry_distribution"]
        assert len(industry_dist["data"]) == 1
        assert industry_dist["data"][0]["label"] == "互联网"

    @pytest.mark.asyncio
    async def test_insights_comprehensive(self, db_session: AsyncSession):
        """测试综合数据洞察"""
        # 创建多个用户
        for i in range(5):
            user = await TestDataFactory.create_user(db_session)

            # 创建帖子
            await TestDataFactory.create_post(
                db_session, user.id,
                industry=f"行业{i % 3}",
                city=f"城市{i % 2}",
                risk_status="approved",
                status="normal"
            )

            # 创建 payday config 和工资记录
            from app.models.payday import PaydayConfig
            config = PaydayConfig(
                user_id=user.id,
                job_name="工作",
                payday=10 + i % 20,
                calendar_type="solar"
            )
            db_session.add(config)
            await db_session.commit()
            await db_session.refresh(config)

            await TestDataFactory.create_salary(
                db_session, user.id, config.id,
                amount=5000 + i * 3000
            )

        insights = await get_insights_distributions(db_session)

        # 验证所有分布都有数据
        assert insights["total_posts"] == 5
        assert insights["industry_distribution"]["total"] > 0
        assert insights["city_distribution"]["total"] > 0
        assert insights["salary_range_distribution"]["total"] == 5
        assert insights["payday_distribution"]["total"] == 5
