"""订单号生成工具"""
from datetime import datetime
from typing import Optional

from app.models.point_order import PointOrder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def generate_order_number() -> str:
    """
    生成唯一订单号

    规则：
    - 格式：PO + YYYYMMDD + 6位随机数
    - 示例：PO20260223000001, PO20260223999999

    Returns:
        订单号
    """
    date_str = datetime.utcnow().strftime("%Y%m%d")
    import random
    random_suffix = random.randint(0, 999999)
    return f"PO{date_str}{random_suffix:06d}"


async def is_order_number_exists(db: AsyncSession, order_number: str) -> bool:
    """检查订单号是否已存在"""
    result = await db.execute(
        select(PointOrder).where(PointOrder.order_number == order_number)
    )
    return result.scalar_one_or_none() is not None
