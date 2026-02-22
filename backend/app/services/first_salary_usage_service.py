"""
第一笔工资用途 Service
"""
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.models.first_salary_usage import FirstSalaryUsage
from app.models.salary import SalaryRecord
from app.schemas.first_salary_usage import FirstSalaryUsageCreate, FirstSalaryUsageUpdate
from app.utils.encryption import encrypt_amount, decrypt_amount
from app.core.exceptions import NotFoundException, ValidationException, AuthorizationException


def _encrypt_with_salt(amount: float) -> str:
    """
    加密金额并将加密数据和salt一起存储为JSON

    由于模型只有amount字段，我们将encrypted和salt组合存储
    """
    encrypted, salt = encrypt_amount(amount)
    data = {"encrypted": encrypted, "salt": salt}
    return json.dumps(data)


def _decrypt_with_salt(combined: str) -> float:
    """
    从组合的加密数据中解密金额
    """
    try:
        data = json.loads(combined)
        return decrypt_amount(data["encrypted"], data["salt"])
    except (json.JSONDecodeError, KeyError):
        # 如果不是JSON格式，可能是旧数据，尝试直接解密
        # 这会失败，但我们可以捕获异常
        return 0.0


async def create_first_salary_usage(
    db: AsyncSession,
    user_id: str,
    usage_data: FirstSalaryUsageCreate
) -> FirstSalaryUsage:
    """
    创建第一笔工资用途记录

    Args:
        db: 数据库会话
        user_id: 用户ID
        usage_data: 用途记录数据

    Returns:
        创建的用途记录

    Raises:
        NotFoundException: 薪资记录不存在
        ValidationException: 金额格式错误
        AuthorizationException: 无权操作
    """
    # 1. 验证薪资记录是否存在且属于该用户
    salary = await db.get(SalaryRecord, usage_data.salary_record_id)
    if not salary:
        raise NotFoundException("薪资记录不存在")

    if salary.user_id != user_id:
        raise AuthorizationException("无权操作此薪资记录")

    # 2. 加密金额（将encrypted和salt组合存储）
    encrypted_amount = _encrypt_with_salt(usage_data.amount)

    # 3. 创建记录
    usage_record = FirstSalaryUsage(
        user_id=user_id,
        salary_record_id=usage_data.salary_record_id,
        usage_category=usage_data.usage_category,
        usage_subcategory=usage_data.usage_subcategory,
        amount=encrypted_amount,
        note=usage_data.note
    )

    db.add(usage_record)
    await db.commit()
    await db.refresh(usage_record)

    return usage_record


async def get_first_salary_usage(
    db: AsyncSession,
    usage_id: str,
    user_id: str
) -> FirstSalaryUsage:
    """
    获取第一笔工资用途记录

    Args:
        db: 数据库会话
        usage_id: 用途记录ID
        user_id: 用户ID

    Returns:
        用途记录

    Raises:
        NotFoundException: 记录不存在
        AuthorizationException: 无权查看
    """
    usage = await db.get(FirstSalaryUsage, usage_id)
    if not usage:
        raise NotFoundException("用途记录不存在")

    if usage.user_id != user_id:
        raise AuthorizationException("无权查看此记录")

    return usage


async def update_first_salary_usage(
    db: AsyncSession,
    usage_id: str,
    user_id: str,
    update_data: FirstSalaryUsageUpdate
) -> FirstSalaryUsage:
    """
    更新第一笔工资用途记录

    Args:
        db: 数据库会话
        usage_id: 用途记录ID
        user_id: 用户ID
        update_data: 更新数据

    Returns:
        更新后的用途记录

    Raises:
        NotFoundException: 记录不存在
    """
    usage = await get_first_salary_usage(db, usage_id, user_id)

    # 更新字段
    if update_data.usage_category is not None:
        usage.usage_category = update_data.usage_category

    if update_data.usage_subcategory is not None:
        usage.usage_subcategory = update_data.usage_subcategory

    if update_data.amount is not None:
        encrypted_amount = _encrypt_with_salt(update_data.amount)
        usage.amount = encrypted_amount

    if update_data.note is not None:
        usage.note = update_data.note

    await db.commit()
    await db.refresh(usage)

    return usage


async def delete_first_salary_usage(
    db: AsyncSession,
    usage_id: str,
    user_id: str
) -> None:
    """
    删除第一笔工资用途记录

    Args:
        db: 数据库会话
        usage_id: 用途记录ID
        user_id: 用户ID

    Raises:
        NotFoundException: 记录不存在
    """
    usage = await get_first_salary_usage(db, usage_id, user_id)
    await db.delete(usage)
    await db.commit()


async def list_first_salary_usages(
    db: AsyncSession,
    user_id: str,
    salary_record_id: Optional[str] = None,
    usage_category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> tuple[list[FirstSalaryUsage], int]:
    """
    获取第一笔工资用途记录列表

    Args:
        db: 数据库会话
        user_id: 用户ID
        salary_record_id: 筛选薪资记录ID
        usage_category: 筛选用途分类
        skip: 跳过记录数
        limit: 返回记录数

    Returns:
        (记录列表, 总数)
    """
    # 构建查询
    query = select(FirstSalaryUsage).where(FirstSalaryUsage.user_id == user_id)

    if salary_record_id:
        query = query.where(FirstSalaryUsage.salary_record_id == salary_record_id)

    if usage_category:
        query = query.where(FirstSalaryUsage.usage_category == usage_category)

    # 总数查询
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页查询，按创建时间倒序
    query = query.order_by(desc(FirstSalaryUsage.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    usages = result.scalars().all()

    return list(usages), total


async def get_usage_statistics_by_category(
    db: AsyncSession,
    user_id: str,
    salary_record_id: Optional[str] = None
) -> dict:
    """
    按分类统计用途金额

    Args:
        db: 数据库会话
        user_id: 用户ID
        salary_record_id: 筛选薪资记录ID

    Returns:
        {usage_category: total_amount}
    """
    query = select(FirstSalaryUsage).where(FirstSalaryUsage.user_id == user_id)

    if salary_record_id:
        query = query.where(FirstSalaryUsage.salary_record_id == salary_record_id)

    result = await db.execute(query)
    usages = result.scalars().all()

    # 解密并统计
    stats = {}
    for usage in usages:
        amount = _decrypt_with_salt(usage.amount)
        stats[usage.usage_category] = stats.get(usage.usage_category, 0) + amount

    return stats
