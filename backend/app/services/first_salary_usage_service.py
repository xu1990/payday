"""
First Salary Usage Service - 第一笔工资用途业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models.first_salary_usage import FirstSalaryUsage
from app.schemas.first_salary_usage import FirstSalaryUsageCreate


async def create_first_salary_usage_records(
    db: AsyncSession,
    user_id: str,
    salary_record_id: str,
    usages: List[dict]
) -> List[FirstSalaryUsage]:
    """
    创建第一笔工资用途记录

    Args:
        db: 数据库会话
        user_id: 用户ID
        salary_record_id: 工资记录ID
        usages: 用途数据列表

    Returns:
        创建的用途记录列表
    """
    from app.utils.logger import get_logger
    logger = get_logger(__name__)

    created_records = []

    for usage_data in usages:
        record = FirstSalaryUsage(
            user_id=user_id,
            salary_record_id=salary_record_id,
            usage_category=usage_data["usageCategory"],
            usage_subcategory=usage_data.get("usageSubcategory"),
            amount=usage_data["amount"],
            note=usage_data.get("note"),
            is_first_salary=1
        )
        db.add(record)
        created_records.append(record)

    await db.commit()

    # 刷新所有记录以获取生成的值
    for record in created_records:
        await db.refresh(record)

    logger.info(f"Created {len(created_records)} first salary usage records for user {user_id}")
    return created_records


async def get_first_salary_usage_by_salary(
    db: AsyncSession,
    salary_record_id: str,
    user_id: str
) -> List[FirstSalaryUsage]:
    """
    根据工资记录ID获取第一笔工资用途（仅限当前用户）

    Args:
        db: 数据库会话
        salary_record_id: 工资记录ID
        user_id: 用户ID（用于权限验证）

    Returns:
        用途记录列表
    """
    stmt = (
        select(FirstSalaryUsage)
        .where(FirstSalaryUsage.salary_record_id == salary_record_id)
        .where(FirstSalaryUsage.user_id == user_id)  # 添加用户ID过滤
        .order_by(FirstSalaryUsage.created_at)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_first_salary_usage_by_user(
    db: AsyncSession,
    user_id: str
) -> List[FirstSalaryUsage]:
    """
    根据用户ID获取第一笔工资用途

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        用途记录列表
    """
    stmt = (
        select(FirstSalaryUsage)
        .where(FirstSalaryUsage.user_id == user_id)
        .where(FirstSalaryUsage.is_first_salary == 1)
        .order_by(FirstSalaryUsage.created_at)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def check_user_has_first_salary_usage(
    db: AsyncSession,
    user_id: str
) -> bool:
    """
    检查用户是否已经有第一笔工资用途记录

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        是否已有记录
    """
    stmt = (
        select(FirstSalaryUsage)
        .where(FirstSalaryUsage.user_id == user_id)
        .where(FirstSalaryUsage.is_first_salary == 1)
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
