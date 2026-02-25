"""
订单分析服务 (Analytics Service)

处理订单数据分析和报表生成：
1. get_order_statistics - 订单统计（总数、总金额、平均订单值、转化率）
2. get_sales_by_product - 商品销售排行（销量、销售额）
3. get_sales_by_category - 分类销售统计（按分类汇总）
4. get_user_order_summary - 用户订单汇总（订单数、总消费、最新订单）
5. get_daily_revenue - 每日收入趋势（日期、收入、订单数）
6. get_order_status_breakdown - 订单状态分布（各状态数量、占比）
7. get_payment_method_stats - 支付方式统计（各方式金额、占比）

关键特性：
- 日期范围过滤：支持灵活的时间范围查询
- 数据聚合：高效的SQL聚合查询
- 性能优化：利用数据库索引，支持大数据集
- 图表格式化：返回适合图表展示的数据格式
- 空值处理：妥善处理无数据情况
- 百分比计算：自动计算各维度占比

性能优化：
- 使用索引字段过滤（created_at, status, payment_status）
- 聚合查询减少数据传输
- 限制返回结果集大小（limit参数）
- 使用高效的SQLAlchemy ORM查询

使用示例：
    ```python
    service = AnalyticsService(redis_client=redis)

    # 获取订单统计
    stats = await service.get_order_statistics(db, date(2026, 1, 1), date(2026, 1, 31))

    # 获取商品销售排行
    top_products = await service.get_sales_by_product(db, date(2026, 1, 1), date(2026, 1, 31), limit=10)

    # 获取每日收入
    daily_revenue = await service.get_daily_revenue(db, days=30)
    ```
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from app.core.exceptions import ValidationException
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductCategory
from app.models.user import User
from sqlalchemy import and_, case, desc, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    订单分析服务

    提供订单数据的统计分析和报表生成功能，支持多维度数据查询和图表数据格式化。

    Attributes:
        redis_client: Redis客户端实例，用于缓存分析结果

    Example:
        ```python
        service = AnalyticsService(redis_client=redis)

        # 订单统计
        stats = await service.get_order_statistics(
            db,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        # 商品销售排行
        top_products = await service.get_sales_by_product(
            db,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            limit=10
        )
        ```
    """

    def __init__(self, redis_client=None):
        """
        初始化AnalyticsService

        Args:
            redis_client: Redis客户端实例，用于缓存分析结果
        """
        self.redis_client = redis_client

    async def get_order_statistics(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        获取订单统计信息

        统计指定日期范围内的订单数据，包括：
        - 总订单数
        - 总收入（已完成订单的final_amount总和）
        - 平均订单值（总收入/订单数）
        - 转化率（已完成订单数/总订单数）

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict: 订单统计信息
                {
                    "total_orders": int,           # 总订单数
                    "completed_orders": int,       # 已完成订单数
                    "total_revenue": Decimal,      # 总收入（分）
                    "average_order_value": Decimal, # 平均订单值（分）
                    "conversion_rate": Decimal      # 转化率（百分比）
                }

        Raises:
            ValidationException: 如果日期范围无效

        Example:
            ```python
            stats = await service.get_order_statistics(
                db,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31)
            )
            print(f"总收入: {stats['total_revenue']}元")
            print(f"转化率: {stats['conversion_rate']}%")
            ```
        """
        # 验证日期范围
        if start_date > end_date:
            raise ValidationException(
                "开始日期不能晚于结束日期",
                details={"start_date": str(start_date), "end_date": str(end_date)}
            )

        logger.info(f"获取订单统计: {start_date} 到 {end_date}")

        # 转换为datetime范围（使用UTC时间）
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 1. 总订单数
        total_orders_result = await db.execute(
            select(func.count())
            .select_from(Order)
            .where(Order.created_at >= start_datetime)
            .where(Order.created_at <= end_datetime)
        )
        total_orders = total_orders_result.scalar_one_or_none() or 0

        # 2. 已完成订单数
        completed_orders_result = await db.execute(
            select(func.count())
            .select_from(Order)
            .where(Order.created_at >= start_datetime)
            .where(Order.created_at <= end_datetime)
            .where(Order.status == "completed")
        )
        completed_orders = completed_orders_result.scalar_one_or_none() or 0

        # 3. 总收入（已完成订单）
        total_revenue_result = await db.execute(
            select(func.sum(Order.final_amount))
            .select_from(Order)
            .where(Order.created_at >= start_datetime)
            .where(Order.created_at <= end_datetime)
            .where(Order.status == "completed")
            .where(Order.payment_status == "paid")
        )
        total_revenue = total_revenue_result.scalar_one_or_none() or Decimal("0")

        # 4. 平均订单值
        average_order_value = (
            total_revenue / completed_orders
            if completed_orders > 0
            else Decimal("0")
        )

        # 5. 转化率（已完成/总数）
        conversion_rate = (
            (Decimal(completed_orders) / Decimal(total_orders) * 100)
            if total_orders > 0
            else Decimal("0")
        )

        return {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "total_revenue": total_revenue.quantize(Decimal("0.01")),
            "average_order_value": average_order_value.quantize(Decimal("0.01")),
            "conversion_rate": conversion_rate.quantize(Decimal("0.01")),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    async def get_sales_by_product(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取商品销售排行

        统计指定日期范围内各商品的销售情况，按销售额降序排列。

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回结果数量限制

        Returns:
            List[Dict]: 商品销售排行
                [
                    {
                        "product_id": str,
                        "product_name": str,
                        "total_revenue": Decimal,  # 总销售额（分）
                        "total_quantity": int,     # 总销量
                        "average_price": Decimal   # 平均单价（分）
                    },
                    ...
                ]

        Example:
            ```python
            top_products = await service.get_sales_by_product(
                db,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                limit=10
            )
            for product in top_products:
                print(f"{product['product_name']}: {product['total_revenue']}元")
            ```
        """
        # 验证日期范围
        if start_date > end_date:
            raise ValidationException(
                "开始日期不能晚于结束日期",
                details={"start_date": str(start_date), "end_date": str(end_date)}
            )

        logger.info(f"获取商品销售排行: {start_date} 到 {end_date}, limit={limit}")

        # 转换为datetime范围
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 查询订单明细，按商品聚合
        query = (
            select(
                OrderItem.product_id,
                OrderItem.product_name,
                func.sum(OrderItem.subtotal).label("total_revenue"),
                func.sum(OrderItem.quantity).label("total_quantity"),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.created_at >= start_datetime)
            .where(Order.created_at <= end_datetime)
            .where(Order.status.in_(["completed", "delivered"]))  # 只统计成功订单
            .where(Order.payment_status == "paid")
            .group_by(OrderItem.product_id, OrderItem.product_name)
            .order_by(desc(func.sum(OrderItem.subtotal)))
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        sales_data = []
        for row in rows:
            product_id, product_name, total_revenue, total_quantity = row

            # 计算平均单价
            average_price = (
                total_revenue / total_quantity
                if total_quantity > 0
                else Decimal("0")
            )

            sales_data.append({
                "product_id": product_id,
                "product_name": product_name,
                "total_revenue": total_revenue.quantize(Decimal("0.01")),
                "total_quantity": total_quantity,
                "average_price": average_price.quantize(Decimal("0.01")),
            })

        return sales_data

    async def get_sales_by_category(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        获取分类销售统计

        统计指定日期范围内各分类的销售情况，包括销售额、销量和占比。

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[Dict]: 分类销售统计
                [
                    {
                        "category_id": str,
                        "category_name": str,
                        "total_revenue": Decimal,  # 总销售额（分）
                        "total_quantity": int,     # 总销量
                        "percentage": Decimal       # 占比（百分比）
                    },
                    ...
                ]

        Example:
            ```python
            category_sales = await service.get_sales_by_category(
                db,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31)
            )
            for category in category_sales:
                print(f"{category['category_name']}: {category['percentage']}%")
            ```
        """
        # 验证日期范围
        if start_date > end_date:
            raise ValidationException(
                "开始日期不能晚于结束日期",
                details={"start_date": str(start_date), "end_date": str(end_date)}
            )

        logger.info(f"获取分类销售统计: {start_date} 到 {end_date}")

        # 转换为datetime范围
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 查询各分类的销售数据
        query = (
            select(
                ProductCategory.id,
                ProductCategory.name,
                func.sum(OrderItem.subtotal).label("total_revenue"),
                func.sum(OrderItem.quantity).label("total_quantity"),
            )
            .join(Product, ProductCategory.id == Product.category_id)
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.created_at >= start_datetime)
            .where(Order.created_at <= end_datetime)
            .where(Order.status.in_(["completed", "delivered"]))
            .where(Order.payment_status == "paid")
            .group_by(ProductCategory.id, ProductCategory.name)
            .order_by(desc(func.sum(OrderItem.subtotal)))
        )

        result = await db.execute(query)
        rows = result.all()

        # 计算总收入（用于占比计算）
        total_revenue_all = sum(row[2] for row in rows) if rows else Decimal("0")

        sales_data = []
        for row in rows:
            category_id, category_name, total_revenue, total_quantity = row

            # 计算占比
            percentage = (
                (total_revenue / total_revenue_all * 100)
                if total_revenue_all > 0
                else Decimal("0")
            )

            sales_data.append({
                "category_id": category_id,
                "category_name": category_name,
                "total_revenue": total_revenue.quantize(Decimal("0.01")),
                "total_quantity": total_quantity,
                "percentage": percentage.quantize(Decimal("0.01")),
            })

        return sales_data

    async def get_user_order_summary(
        self,
        db: AsyncSession,
        user_id: str
    ) -> Dict:
        """
        获取用户订单汇总

        统计指定用户的订单数据，包括订单总数、总消费金额、最新订单等。

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Dict: 用户订单汇总
                {
                    "user_id": str,
                    "total_orders": int,           # 订单总数
                    "total_spent": Decimal,         # 总消费（分）
                    "average_order_value": Decimal, # 平均订单值（分）
                    "latest_order_date": datetime,  # 最新订单日期
                    "recent_orders": List[Dict]     # 最近5条订单
                }

        Example:
            ```python
            summary = await service.get_user_order_summary(db, "user_123")
            print(f"用户总订单数: {summary['total_orders']}")
            print(f"用户总消费: {summary['total_spent']}元")
            ```
        """
        logger.info(f"获取用户订单汇总: user_id={user_id}")

        # 1. 订单总数
        total_orders_result = await db.execute(
            select(func.count())
            .select_from(Order)
            .where(Order.user_id == user_id)
        )
        total_orders = total_orders_result.scalar_one_or_none() or 0

        # 2. 总消费（已完成订单）
        total_spent_result = await db.execute(
            select(func.sum(Order.final_amount))
            .select_from(Order)
            .where(Order.user_id == user_id)
            .where(Order.status == "completed")
            .where(Order.payment_status == "paid")
        )
        total_spent = total_spent_result.scalar_one_or_none() or Decimal("0")

        # 3. 平均订单值
        average_order_value = (
            total_spent / total_orders
            if total_orders > 0
            else Decimal("0")
        )

        # 4. 最新订单日期
        latest_order_result = await db.execute(
            select(func.max(Order.created_at))
            .select_from(Order)
            .where(Order.user_id == user_id)
        )
        latest_order_date = latest_order_result.scalar_one_or_none()

        # 5. 最近5条订单
        recent_orders_result = await db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(desc(Order.created_at))
            .limit(5)
        )
        recent_orders = recent_orders_result.scalars().all()

        recent_orders_data = []
        for order in recent_orders:
            recent_orders_data.append({
                "order_id": order.id,
                "order_number": order.order_number,
                "final_amount": str(order.final_amount),
                "status": order.status,
                "payment_status": order.payment_status,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            })

        return {
            "user_id": user_id,
            "total_orders": total_orders,
            "total_spent": total_spent.quantize(Decimal("0.01")),
            "average_order_value": average_order_value.quantize(Decimal("0.01")),
            "latest_order_date": latest_order_date.isoformat() if latest_order_date else None,
            "recent_orders": recent_orders_data,
        }

    async def get_daily_revenue(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> List[Dict]:
        """
        获取每日收入趋势

        统计最近N天的每日收入数据，用于生成收入趋势图。

        Args:
            db: 数据库会话
            days: 统计天数（默认30天）

        Returns:
            List[Dict]: 每日收入数据
                [
                    {
                        "date": date,           # 日期
                        "revenue": Decimal,     # 当日收入（分）
                        "order_count": int      # 当日订单数
                    },
                    ...
                ]

        Example:
            ```python
            daily_revenue = await service.get_daily_revenue(db, days=7)
            for day in daily_revenue:
                print(f"{day['date']}: {day['revenue']}元 ({day['order_count']}单)")
            ```
        """
        logger.info(f"获取每日收入趋势: days={days}")

        # 计算日期范围
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # 转换为datetime范围
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 按日期聚合查询
        query = (
            select(
                func.date(Order.created_at).label("date"),
                func.sum(Order.final_amount).label("revenue"),
                func.count(Order.id).label("order_count"),
            )
            .where(Order.created_at >= start_datetime)
            .where(Order.created_at <= end_datetime)
            .where(Order.status == "completed")
            .where(Order.payment_status == "paid")
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )

        result = await db.execute(query)
        rows = result.all()

        # 创建日期字典，方便查找
        revenue_dict = {row[0]: {"revenue": row[1], "order_count": row[2]} for row in rows}

        # 生成完整日期序列（填充缺失日期为0）
        daily_data = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            revenue_info = revenue_dict.get(current_date, {"revenue": Decimal("0"), "order_count": 0})

            daily_data.append({
                "date": current_date.isoformat(),
                "revenue": str(revenue_info["revenue"].quantize(Decimal("0.01"))),
                "order_count": revenue_info["order_count"],
            })

        return daily_data

    async def get_order_status_breakdown(
        self,
        db: AsyncSession
    ) -> List[Dict]:
        """
        获取订单状态分布

        统计所有订单的状态分布情况，包括各状态的订单数量和占比。

        Args:
            db: 数据库会话

        Returns:
            List[Dict]: 订单状态分布
                [
                    {
                        "status": str,          # 状态名称
                        "count": int,           # 订单数量
                        "percentage": Decimal   # 占比（百分比）
                    },
                    ...
                ]

        Example:
            ```python
            status_breakdown = await service.get_order_status_breakdown(db)
            for status in status_breakdown:
                print(f"{status['status']}: {status['count']}单 ({status['percentage']}%)")
            ```
        """
        logger.info("获取订单状态分布")

        # 按状态统计订单数量
        query = (
            select(Order.status, func.count(Order.id).label("count"))
            .group_by(Order.status)
            .order_by(func.count(Order.id).desc())
        )

        result = await db.execute(query)
        rows = result.all()

        # 计算总订单数
        total_orders = sum(row[1] for row in rows) if rows else 0

        status_data = []
        for row in rows:
            status, count = row

            # 计算占比
            percentage = (
                (Decimal(count) / total_orders * 100)
                if total_orders > 0
                else Decimal("0")
            )

            status_data.append({
                "status": status,
                "count": count,
                "percentage": percentage.quantize(Decimal("0.01")),
            })

        return status_data

    async def get_payment_method_stats(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        获取支付方式统计

        统计指定日期范围内各支付方式的使用情况，包括金额、订单数和占比。

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[Dict]: 支付方式统计
                [
                    {
                        "payment_method": str,  # 支付方式
                        "total_amount": Decimal, # 总金额（分）
                        "order_count": int,      # 订单数
                        "percentage": Decimal    # 占比（百分比）
                    },
                    ...
                ]

        Example:
            ```python
            payment_stats = await service.get_payment_method_stats(
                db,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31)
            )
            for method in payment_stats:
                print(f"{method['payment_method']}: {method['total_amount']}元 ({method['percentage']}%)")
            ```
        """
        # 验证日期范围
        if start_date > end_date:
            raise ValidationException(
                "开始日期不能晚于结束日期",
                details={"start_date": str(start_date), "end_date": str(end_date)}
            )

        logger.info(f"获取支付方式统计: {start_date} 到 {end_date}")

        # 转换为datetime范围
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 按支付方式统计
        query = (
            select(
                Order.payment_method,
                func.sum(Order.final_amount).label("total_amount"),
                func.count(Order.id).label("order_count"),
            )
            .where(Order.created_at >= start_datetime)
            .where(Order.created_at <= end_datetime)
            .where(Order.payment_status == "paid")
            .group_by(Order.payment_method)
            .order_by(desc(func.sum(Order.final_amount)))
        )

        result = await db.execute(query)
        rows = result.all()

        # 计算总金额（用于占比计算）
        total_amount_all = sum(row[1] for row in rows) if rows else Decimal("0")

        payment_data = []
        for row in rows:
            payment_method, total_amount, order_count = row

            # 计算占比
            percentage = (
                (total_amount / total_amount_all * 100)
                if total_amount_all > 0
                else Decimal("0")
            )

            payment_data.append({
                "payment_method": payment_method,
                "total_amount": total_amount.quantize(Decimal("0.01")),
                "order_count": order_count,
                "percentage": percentage.quantize(Decimal("0.01")),
            })

        return payment_data

    async def get_revenue_comparison(
        self,
        db: AsyncSession,
        current_start: date,
        current_end: date,
        comparison_start: date = None,
        comparison_end: date = None
    ) -> Dict:
        """
        获取收入对比分析

        对比两个时间段内的收入情况，计算增长率。

        Args:
            db: 数据库会话
            current_start: 当前时段开始日期
            current_end: 当前时段结束日期
            comparison_start: 对比时段开始日期（可选，默认为上一周期）
            comparison_end: 对比时段结束日期（可选，默认为上一周期）

        Returns:
            Dict: 收入对比分析
                {
                    "current_period": {
                        "start_date": date,
                        "end_date": date,
                        "total_revenue": Decimal,
                        "order_count": int
                    },
                    "comparison_period": {
                        "start_date": date,
                        "end_date": date,
                        "total_revenue": Decimal,
                        "order_count": int
                    },
                    "growth_rate": Decimal  # 增长率（百分比）
                }

        Example:
            ```python
            # 对比本月和上月
            comparison = await service.get_revenue_comparison(
                db,
                current_start=date(2026, 2, 1),
                current_end=date(2026, 2, 28)
            )
            print(f"增长率: {comparison['growth_rate']}%")
            ```
        """
        logger.info(f"获取收入对比: {current_start}-{current_end}")

        # 如果未指定对比时段，计算上一周期
        if not comparison_start or not comparison_end:
            days_diff = (current_end - current_start).days
            comparison_end = current_start - timedelta(days=1)
            comparison_start = comparison_end - timedelta(days=days_diff)

        # 获取当前时段数据
        current_stats = await self.get_order_statistics(db, current_start, current_end)

        # 获取对比时段数据
        comparison_stats = await self.get_order_statistics(db, comparison_start, comparison_end)

        # 计算增长率
        current_revenue = current_stats["total_revenue"]
        comparison_revenue = comparison_stats["total_revenue"]

        if comparison_revenue > 0:
            growth_rate = (
                (current_revenue - comparison_revenue) / comparison_revenue * 100
            )
        else:
            growth_rate = (
                Decimal("100") if current_revenue > 0 else Decimal("0")
            )

        return {
            "current_period": {
                "start_date": current_start.isoformat(),
                "end_date": current_end.isoformat(),
                "total_revenue": current_stats["total_revenue"],
                "order_count": current_stats["completed_orders"],
            },
            "comparison_period": {
                "start_date": comparison_start.isoformat(),
                "end_date": comparison_end.isoformat(),
                "total_revenue": comparison_stats["total_revenue"],
                "order_count": comparison_stats["completed_orders"],
            },
            "growth_rate": growth_rate.quantize(Decimal("0.01")),
        }
