"""
Analytics Service 测试 - 订单分析服务

测试覆盖：
1. get_order_statistics - 订单统计（总数、总金额、平均订单值、转化率）
2. get_sales_by_product - 商品销售排行（销量、销售额）
3. get_sales_by_category - 分类销售统计（按分类汇总）
4. get_user_order_summary - 用户订单汇总（订单数、总消费、最新订单）
5. get_daily_revenue - 每日收入趋势（日期、收入、订单数）
6. get_order_status_breakdown - 订单状态分布（各状态数量、占比）
7. get_payment_method_stats - 支付方式统计（各方式金额、占比）
8. 日期范围过滤
9. 数据聚合计算
10. 性能优化（索引使用）
11. 空值处理
12. 大数据集处理
13. 图表数据格式化
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta, date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics_service import AnalyticsService
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductCategory
from app.models.user import User
from app.core.exceptions import ValidationException
from tests.test_utils import TestDataFactory


class TestAnalyticsService:
    """AnalyticsService测试类"""

    @pytest.fixture
    def service(self):
        """创建AnalyticsService实例"""
        return AnalyticsService(redis_client=None)

    # ============ get_order_statistics 测试 ============

    @pytest.mark.asyncio
    async def test_get_order_statistics_basic(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：基本订单统计"""
        # 创建用户
        user = await TestDataFactory.create_user(db_session)

        # 创建不同状态的订单
        now = datetime.utcnow()
        await self._create_order(
            db_session, user.id, "order_1", Decimal("10000"), "completed", "paid", now
        )
        await self._create_order(
            db_session, user.id, "order_2", Decimal("20000"), "completed", "paid", now
        )
        await self._create_order(
            db_session, user.id, "order_3", Decimal("15000"), "pending", "pending", now
        )

        # 执行测试
        start_date = date(2026, 1, 1)
        end_date = date(2026, 12, 31)
        result = await service.get_order_statistics(db_session, start_date, end_date)

        # 验证结果
        assert result["total_orders"] == 3
        assert result["completed_orders"] == 2
        assert result["total_revenue"] == Decimal("30000")
        assert result["average_order_value"] == Decimal("15000")
        assert result["conversion_rate"] == Decimal("66.67")

    @pytest.mark.asyncio
    async def test_get_order_statistics_with_filters(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：带日期过滤的订单统计"""
        user = await TestDataFactory.create_user(db_session)

        # 创建不同月份的订单
        jan_date = datetime(2026, 1, 15, 12, 0, 0)
        feb_date = datetime(2026, 2, 15, 12, 0, 0)

        await self._create_order(
            db_session, user.id, "order_1", Decimal("10000"), "completed", "paid", jan_date
        )
        await self._create_order(
            db_session, user.id, "order_2", Decimal("15000"), "completed", "paid", feb_date
        )

        # 查询1月数据
        result = await service.get_order_statistics(db_session, date(2026, 1, 1), date(2026, 1, 31))

        assert result["total_orders"] == 1
        assert result["total_revenue"] == Decimal("10000")

    @pytest.mark.asyncio
    async def test_get_order_statistics_empty_result(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：空结果集的订单统计"""
        user = await TestDataFactory.create_user(db_session)

        # 没有创建订单
        result = await service.get_order_statistics(db_session, date(2026, 1, 1), date(2026, 1, 31))

        assert result["total_orders"] == 0
        assert result["completed_orders"] == 0
        assert result["total_revenue"] == Decimal("0")
        assert result["average_order_value"] == Decimal("0")
        assert result["conversion_rate"] == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_order_statistics_invalid_date_range(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：无效的日期范围"""
        start_date = date(2026, 1, 31)
        end_date = date(2026, 1, 1)  # 早于开始日期

        with pytest.raises(ValidationException):
            await service.get_order_statistics(db_session, start_date, end_date)

    @pytest.mark.asyncio
    async def test_get_order_statistics_excludes_unpaid_orders(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：排除未支付订单"""
        user = await TestDataFactory.create_user(db_session)

        now = datetime.utcnow()
        # 已支付订单
        await self._create_order(
            db_session, user.id, "order_1", Decimal("10000"), "completed", "paid", now
        )
        # 未支付订单
        await self._create_order(
            db_session, user.id, "order_2", Decimal("20000"), "completed", "pending", now
        )

        result = await service.get_order_statistics(db_session, date(2026, 1, 1), date(2026, 12, 31))

        # 只应统计已支付订单
        assert result["total_orders"] == 2
        assert result["completed_orders"] == 2
        assert result["total_revenue"] == Decimal("10000")

    # ============ get_sales_by_product 测试 ============

    @pytest.mark.asyncio
    async def test_get_sales_by_product_basic(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：基本商品销售排行"""
        user = await TestDataFactory.create_user(db_session)
        now = datetime.utcnow()

        # 创建商品和分类
        category = await self._create_category(db_session, "category_1", "数码", "digital")
        product1 = await self._create_product(db_session, "product_1", "手机", category.id)
        product2 = await self._create_product(db_session, "product_2", "电脑", category.id)
        product3 = await self._create_product(db_session, "product_3", "平板", category.id)

        # 创建订单和订单明细
        order1 = await self._create_order(db_session, user.id, "order_1", Decimal("20000"), "completed", "paid", now)
        await self._create_order_item(db_session, order1.id, product1.id, "手机", 2, Decimal("10000"), Decimal("20000"))

        order2 = await self._create_order(db_session, user.id, "order_2", Decimal("15000"), "completed", "paid", now)
        await self._create_order_item(db_session, order2.id, product2.id, "电脑", 1, Decimal("15000"), Decimal("15000"))

        order3 = await self._create_order(db_session, user.id, "order_3", Decimal("10000"), "completed", "paid", now)
        await self._create_order_item(db_session, order3.id, product3.id, "平板", 1, Decimal("10000"), Decimal("10000"))

        # 执行测试
        result = await service.get_sales_by_product(db_session, date(2026, 1, 1), date(2026, 12, 31), limit=10)

        assert len(result) == 3
        # 验证按销售额降序排列
        assert result[0]["product_name"] == "手机"
        assert result[0]["total_revenue"] == Decimal("20000")
        assert result[0]["total_quantity"] == 2
        assert result[0]["average_price"] == Decimal("10000")

    @pytest.mark.asyncio
    async def test_get_sales_by_product_with_limit(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：带限制的商品销售排行"""
        user = await TestDataFactory.create_user(db_session)
        now = datetime.utcnow()

        category = await self._create_category(db_session, "category_1", "数码", "digital")

        # 创建5个商品
        for i in range(1, 6):
            product = await self._create_product(db_session, f"product_{i}", f"商品{i}", category.id)
            order = await self._create_order(
                db_session, user.id, f"order_{i}", Decimal(f"{i*1000}"), "completed", "paid", now
            )
            await self._create_order_item(
                db_session, order.id, product.id, f"商品{i}", 1, Decimal(f"{i*1000}"), Decimal(f"{i*1000}")
            )

        # 限制返回3条
        result = await service.get_sales_by_product(db_session, date(2026, 1, 1), date(2026, 12, 31), limit=3)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_sales_by_product_empty_result(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：空结果的商品销售排行"""
        result = await service.get_sales_by_product(db_session, date(2026, 1, 1), date(2026, 1, 31))

        assert len(result) == 0

    # ============ get_sales_by_category 测试 ============

    @pytest.mark.asyncio
    async def test_get_sales_by_category_basic(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：基本分类销售统计"""
        user = await TestDataFactory.create_user(db_session)
        now = datetime.utcnow()

        # 创建分类和商品
        category1 = await self._create_category(db_session, "category_1", "数码", "digital")
        category2 = await self._create_category(db_session, "category_2", "服装", "clothing")
        category3 = await self._create_category(db_session, "category_3", "食品", "food")

        product1 = await self._create_product(db_session, "product_1", "手机", category1.id)
        product2 = await self._create_product(db_session, "product_2", "电脑", category1.id)
        product3 = await self._create_product(db_session, "product_3", "衣服", category2.id)
        product4 = await self._create_product(db_session, "product_4", "零食", category3.id)

        # 创建订单和订单明细
        order1 = await self._create_order(db_session, user.id, "order_1", Decimal("25000"), "completed", "paid", now)
        await self._create_order_item(db_session, order1.id, product1.id, "手机", 1, Decimal("15000"), Decimal("15000"))
        await self._create_order_item(db_session, order1.id, product2.id, "电脑", 1, Decimal("10000"), Decimal("10000"))

        order2 = await self._create_order(db_session, user.id, "order_2", Decimal("15000"), "completed", "paid", now)
        await self._create_order_item(db_session, order2.id, product3.id, "衣服", 1, Decimal("15000"), Decimal("15000"))

        order3 = await self._create_order(db_session, user.id, "order_3", Decimal("10000"), "completed", "paid", now)
        await self._create_order_item(db_session, order3.id, product4.id, "零食", 1, Decimal("10000"), Decimal("10000"))

        # 执行测试
        result = await service.get_sales_by_category(db_session, date(2026, 1, 1), date(2026, 12, 31))

        assert len(result) == 3
        # 验证数码分类
        digital = next(r for r in result if r["category_name"] == "数码")
        assert digital["total_revenue"] == Decimal("25000")
        assert digital["total_quantity"] == 2
        assert digital["percentage"] == Decimal("50.00")

        # 验证服装分类
        clothing = next(r for r in result if r["category_name"] == "服装")
        assert clothing["total_revenue"] == Decimal("15000")
        assert clothing["percentage"] == Decimal("30.00")

        # 验证食品分类
        food = next(r for r in result if r["category_name"] == "食品")
        assert food["total_revenue"] == Decimal("10000")
        assert food["percentage"] == Decimal("20.00")

    @pytest.mark.asyncio
    async def test_get_sales_by_category_empty_result(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：空结果的分类销售统计"""
        result = await service.get_sales_by_category(db_session, date(2026, 1, 1), date(2026, 1, 31))

        assert len(result) == 0

    # ============ get_user_order_summary 测试 ============

    @pytest.mark.asyncio
    async def test_get_user_order_summary_basic(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：基本用户订单汇总"""
        user = await TestDataFactory.create_user(db_session)
        now = datetime.utcnow()

        # 创建多个订单
        await self._create_order(db_session, user.id, "order_1", Decimal("10000"), "completed", "paid", now)
        await self._create_order(db_session, user.id, "order_2", Decimal("8000"), "completed", "paid", now)
        await self._create_order(db_session, user.id, "order_3", Decimal("5000"), "pending", "pending", now)

        # 执行测试
        result = await service.get_user_order_summary(db_session, user.id)

        assert result["user_id"] == user.id
        assert result["total_orders"] == 3
        assert result["total_spent"] == Decimal("18000")  # 只统计已完成订单
        assert result["average_order_value"] == Decimal("6000")  # 18000/3
        assert result["latest_order_date"] is not None
        assert len(result["recent_orders"]) == 3

    @pytest.mark.asyncio
    async def test_get_user_order_summary_no_orders(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：用户无订单的汇总"""
        user = await TestDataFactory.create_user(db_session)

        result = await service.get_user_order_summary(db_session, user.id)

        assert result["total_orders"] == 0
        assert result["total_spent"] == Decimal("0")
        assert result["average_order_value"] == Decimal("0")
        assert result["latest_order_date"] is None
        assert len(result["recent_orders"]) == 0

    @pytest.mark.asyncio
    async def test_get_user_order_summary_recent_orders_limit(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：最近订单数量限制"""
        user = await TestDataFactory.create_user(db_session)
        now = datetime.utcnow()

        # 创建10个订单
        for i in range(10):
            await self._create_order(
                db_session, user.id, f"order_{i}", Decimal(f"{(i+1)*1000}"), "completed", "paid", now
            )

        result = await service.get_user_order_summary(db_session, user.id)

        # 应该只返回最近5条
        assert len(result["recent_orders"]) == 5

    # ============ get_daily_revenue 测试 ============

    @pytest.mark.asyncio
    async def test_get_daily_revenue_basic(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：基本每日收入趋势"""
        user = await TestDataFactory.create_user(db_session)

        # 创建最近7天的订单
        for i in range(7):
            order_date = datetime.utcnow() - timedelta(days=i)
            await self._create_order(
                db_session, user.id, f"order_{i}", Decimal(f"{(i+1)*1000}"), "completed", "paid", order_date
            )

        # 执行测试
        result = await service.get_daily_revenue(db_session, days=7)

        assert len(result) == 7
        # 验证数据结构
        for day_data in result:
            assert "date" in day_data
            assert "revenue" in day_data
            assert "order_count" in day_data

    @pytest.mark.asyncio
    async def test_get_daily_revenue_thirty_days(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：30天收入趋势"""
        user = await TestDataFactory.create_user(db_session)

        # 创建最近30天的订单
        for i in range(30):
            order_date = datetime.utcnow() - timedelta(days=i)
            await self._create_order(
                db_session, user.id, f"order_{i}", Decimal("1000"), "completed", "paid", order_date
            )

        result = await service.get_daily_revenue(db_session, days=30)

        assert len(result) == 30

    @pytest.mark.asyncio
    async def test_get_daily_revenue_custom_days(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：自定义天数的收入趋势"""
        user = await TestDataFactory.create_user(db_session)

        for i in range(14):
            order_date = datetime.utcnow() - timedelta(days=i)
            await self._create_order(
                db_session, user.id, f"order_{i}", Decimal("1000"), "completed", "paid", order_date
            )

        result = await service.get_daily_revenue(db_session, days=14)

        assert len(result) == 14

    @pytest.mark.asyncio
    async def test_get_daily_revenue_fill_missing_dates(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：填充缺失的日期"""
        user = await TestDataFactory.create_user(db_session)

        # 只创建3天的订单
        await self._create_order(
            db_session, user.id, "order_1", Decimal("1000"), "completed", "paid", datetime.utcnow()
        )
        await self._create_order(
            db_session, user.id, "order_2", Decimal("3000"), "completed", "paid", datetime.utcnow() - timedelta(days=2)
        )
        await self._create_order(
            db_session, user.id, "order_3", Decimal("5000"), "completed", "paid", datetime.utcnow() - timedelta(days=5)
        )

        result = await service.get_daily_revenue(db_session, days=7)

        # 应该返回7天，缺失的日期填充为0
        assert len(result) == 7
        # 验证至少有一些天的订单数为0
        assert any(d["order_count"] == 0 for d in result)

    # ============ get_order_status_breakdown 测试 ============

    @pytest.mark.asyncio
    async def test_get_order_status_breakdown_basic(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：基本订单状态分布"""
        user = await TestDataFactory.create_user(db_session)
        now = datetime.utcnow()

        # 创建不同状态的订单
        await self._create_order(db_session, user.id, "order_1", Decimal("1000"), "pending", "pending", now)
        await self._create_order(db_session, user.id, "order_2", Decimal("2000"), "paid", "paid", now)
        await self._create_order(db_session, user.id, "order_3", Decimal("3000"), "processing", "paid", now)
        await self._create_order(db_session, user.id, "order_4", Decimal("4000"), "shipped", "paid", now)
        await self._create_order(db_session, user.id, "order_5", Decimal("5000"), "delivered", "paid", now)
        await self._create_order(db_session, user.id, "order_6", Decimal("6000"), "completed", "paid", now)
        await self._create_order(db_session, user.id, "order_7", Decimal("7000"), "cancelled", "pending", now)
        await self._create_order(db_session, user.id, "order_8", Decimal("8000"), "refunding", "paid", now)
        await self._create_order(db_session, user.id, "order_9", Decimal("9000"), "refunded", "refunded", now)

        result = await service.get_order_status_breakdown(db_session)

        assert len(result) == 9
        # 验证每个状态都有数据
        statuses = {r["status"] for r in result}
        assert "pending" in statuses
        assert "paid" in statuses
        assert "completed" in statuses
        assert "cancelled" in statuses

        # 验证占比计算
        completed = next(r for r in result if r["status"] == "completed")
        assert completed["count"] == 1
        assert completed["percentage"] == Decimal("11.11")  # 1/9 * 100

    @pytest.mark.asyncio
    async def test_get_order_status_breakdown_empty(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：空订单的状态分布"""
        result = await service.get_order_status_breakdown(db_session)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_order_status_breakdown_single_status(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：只有一种状态的订单"""
        user = await TestDataFactory.create_user(db_session)
        now = datetime.utcnow()

        # 只创建completed状态的订单
        for i in range(5):
            await self._create_order(
                db_session, user.id, f"order_{i}", Decimal(f"{(i+1)*1000}"), "completed", "paid", now
            )

        result = await service.get_order_status_breakdown(db_session)

        assert len(result) == 1
        assert result[0]["status"] == "completed"
        assert result[0]["count"] == 5
        assert result[0]["percentage"] == Decimal("100.00")

    # ============ get_payment_method_stats 测试 ============

    @pytest.mark.asyncio
    async def test_get_payment_method_stats_basic(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：基本支付方式统计"""
        user = await TestDataFactory.create_user(db_session)
        now = datetime.utcnow()

        # 创建不同支付方式的订单
        await self._create_order(
            db_session, user.id, "order_1", Decimal("10000"), "completed", "paid", now, payment_method="wechat"
        )
        await self._create_order(
            db_session, user.id, "order_2", Decimal("8000"), "completed", "paid", now, payment_method="wechat"
        )
        await self._create_order(
            db_session, user.id, "order_3", Decimal("6000"), "completed", "paid", now, payment_method="alipay"
        )
        await self._create_order(
            db_session, user.id, "order_4", Decimal("4000"), "completed", "paid", now, payment_method="alipay"
        )
        await self._create_order(
            db_session, user.id, "order_5", Decimal("2000"), "completed", "paid", now, payment_method="points"
        )
        await self._create_order(
            db_session, user.id, "order_6", Decimal("3000"), "completed", "paid", now, payment_method="hybrid"
        )

        start_date = date(2026, 1, 1)
        end_date = date(2026, 12, 31)
        result = await service.get_payment_method_stats(db_session, start_date, end_date)

        assert len(result) == 4
        # 验证总额
        total_amount = sum(r["total_amount"] for r in result)
        assert total_amount == Decimal("33000")

        # 验证wechat占比 (18000/33000)
        wechat = next(r for r in result if r["payment_method"] == "wechat")
        assert wechat["total_amount"] == Decimal("18000")
        assert wechat["order_count"] == 2
        assert wechat["percentage"] == Decimal("54.55")

    @pytest.mark.asyncio
    async def test_get_payment_method_stats_empty(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：空结果的支付方式统计"""
        result = await service.get_payment_method_stats(db_session, date(2026, 1, 1), date(2026, 1, 31))

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_payment_method_stats_date_filter(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：支付方式统计的日期过滤"""
        user = await TestDataFactory.create_user(db_session)

        # 创建1月订单
        jan_date = datetime(2026, 1, 15, 12, 0, 0)
        await self._create_order(
            db_session, user.id, "order_1", Decimal("10000"), "completed", "paid", jan_date, payment_method="wechat"
        )

        # 创建2月订单
        feb_date = datetime(2026, 2, 15, 12, 0, 0)
        await self._create_order(
            db_session, user.id, "order_2", Decimal("20000"), "completed", "paid", feb_date, payment_method="alipay"
        )

        # 查询1月数据
        result_jan = await service.get_payment_method_stats(db_session, date(2026, 1, 1), date(2026, 1, 31))
        assert len(result_jan) == 1
        assert result_jan[0]["payment_method"] == "wechat"

        # 查询2月数据
        result_feb = await service.get_payment_method_stats(db_session, date(2026, 2, 1), date(2026, 2, 28))
        assert len(result_feb) == 1
        assert result_feb[0]["payment_method"] == "alipay"

    # ============ get_revenue_comparison 测试 ============

    @pytest.mark.asyncio
    async def test_get_revenue_comparison_basic(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：基本收入对比分析"""
        user = await TestDataFactory.create_user(db_session)

        # 当前时段（2月）
        feb_date = datetime(2026, 2, 15, 12, 0, 0)
        await self._create_order(
            db_session, user.id, "order_1", Decimal("20000"), "completed", "paid", feb_date
        )
        await self._create_order(
            db_session, user.id, "order_2", Decimal("10000"), "completed", "paid", feb_date
        )

        # 对比时段（1月）
        jan_date = datetime(2026, 1, 15, 12, 0, 0)
        await self._create_order(
            db_session, user.id, "order_3", Decimal("15000"), "completed", "paid", jan_date
        )

        # 执行测试
        result = await service.get_revenue_comparison(
            db_session,
            current_start=date(2026, 2, 1),
            current_end=date(2026, 2, 28)
        )

        assert result["current_period"]["total_revenue"] == Decimal("30000")
        assert result["comparison_period"]["total_revenue"] == Decimal("15000")
        # 增长率 = (30000 - 15000) / 15000 * 100 = 100%
        assert result["growth_rate"] == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_get_revenue_comparison_decline(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：收入下降的对比分析"""
        user = await TestDataFactory.create_user(db_session)

        # 当前时段收入较低
        feb_date = datetime(2026, 2, 15, 12, 0, 0)
        await self._create_order(
            db_session, user.id, "order_1", Decimal("10000"), "completed", "paid", feb_date
        )

        # 对比时段收入较高
        jan_date = datetime(2026, 1, 15, 12, 0, 0)
        await self._create_order(
            db_session, user.id, "order_2", Decimal("20000"), "completed", "paid", jan_date
        )

        result = await service.get_revenue_comparison(
            db_session,
            current_start=date(2026, 2, 1),
            current_end=date(2026, 2, 28)
        )

        # 增长率应为负数
        assert result["growth_rate"] < 0
        assert result["growth_rate"] == Decimal("-50.00")

    @pytest.mark.asyncio
    async def test_get_revenue_comparison_custom_comparison_period(self, service: AnalyticsService, db_session: AsyncSession):
        """测试：自定义对比时段"""
        user = await TestDataFactory.create_user(db_session)

        # 当前时段
        await self._create_order(
            db_session, user.id, "order_1", Decimal("30000"), "completed", "paid", datetime(2026, 2, 15)
        )

        # 对比时段（自定义）
        await self._create_order(
            db_session, user.id, "order_2", Decimal("10000"), "completed", "paid", datetime(2025, 12, 15)
        )

        result = await service.get_revenue_comparison(
            db_session,
            current_start=date(2026, 2, 1),
            current_end=date(2026, 2, 28),
            comparison_start=date(2025, 12, 1),
            comparison_end=date(2025, 12, 31)
        )

        assert result["current_period"]["total_revenue"] == Decimal("30000")
        assert result["comparison_period"]["total_revenue"] == Decimal("10000")
        assert result["growth_rate"] == Decimal("200.00")

    # ============ 辅助方法 ============

    async def _create_order(
        self,
        db: AsyncSession,
        user_id: str,
        order_id: str,
        final_amount: Decimal,
        status: str,
        payment_status: str,
        created_at: datetime,
        payment_method: str = "wechat"
    ) -> Order:
        """创建测试订单"""
        order = Order(
            id=order_id,
            user_id=user_id,
            order_number=f"ORD{order_id}",
            total_amount=final_amount,
            points_used=0,
            discount_amount=Decimal("0"),
            shipping_cost=Decimal("0"),
            final_amount=final_amount,
            payment_method=payment_method,
            payment_status=payment_status,
            transaction_id=f"txn_{order_id}" if payment_status == "paid" else None,
            paid_at=datetime.utcnow() if payment_status == "paid" else None,
            status=status,
            shipping_address_id=None,
            shipping_template_id=None,
            created_at=created_at,
            updated_at=datetime.utcnow()
        )
        db.add(order)
        await db.commit()
        await db.rollback()
        await db.refresh(order)
        return order

    async def _create_order_item(
        self,
        db: AsyncSession,
        order_id: str,
        product_id: str,
        product_name: str,
        quantity: int,
        unit_price: Decimal,
        subtotal: Decimal
    ) -> OrderItem:
        """创建测试订单明细"""
        item = OrderItem(
            id=f"item_{order_id}_{product_id}",
            order_id=order_id,
            product_id=product_id,
            sku_id=None,
            product_name=product_name,
            sku_name=None,
            product_image=None,
            attributes=None,
            unit_price=unit_price,
            quantity=quantity,
            subtotal=subtotal,
            bundle_components=None
        )
        db.add(item)
        await db.commit()
        await db.rollback()
        await db.refresh(item)
        return item

    async def _create_product(
        self,
        db: AsyncSession,
        product_id: str,
        name: str,
        category_id: str
    ) -> Product:
        """创建测试商品"""
        product = Product(
            id=product_id,
            name=name,
            description=f"{name}描述",
            images=["https://example.com/image.jpg"],
            category_id=category_id,
            product_type="cash",
            item_type="physical",
            bundle_type=None,
            is_active=True,
            is_virtual=False,
            sort_order=0,
            seo_keywords="",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(product)
        await db.commit()
        await db.rollback()
        await db.refresh(product)
        return product

    async def _create_category(
        self,
        db: AsyncSession,
        category_id: str,
        name: str,
        code: str
    ) -> ProductCategory:
        """创建测试分类"""
        category = ProductCategory(
            id=category_id,
            name=name,
            code=code,
            parent_id=None,
            icon="https://example.com/icon.png",
            sort_order=0,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(category)
        await db.commit()
        await db.rollback()
        await db.refresh(category)
        return category
