"""
First Salary Usage API - 第一笔工资用途接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, rate_limit_general
from app.core.exceptions import success_response, ValidationException
from app.models.user import User
from app.schemas.first_salary_usage import FirstSalaryUsageListCreate, FirstSalaryUsageResponse
from app.services.first_salary_usage_service import (
    create_first_salary_usage_records,
    get_first_salary_usage_by_salary,
    get_first_salary_usage_by_user
)

router = APIRouter(prefix="/first-salary-usage", tags=["first-salary-usage"])


@router.post("/{recordId}", dependencies=[Depends(rate_limit_general)])
async def create_first_salary_usage(
    recordId: str,
    body: FirstSalaryUsageListCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建第一笔工资用途记录

    创建第一笔工资用途的分享记录
    """
    from app.utils.logger import get_logger
    logger = get_logger(__name__)

    # 验证至少有一个用途记录
    if not body.usages or len(body.usages) == 0:
        raise ValidationException("至少需要一个用途记录", code="NO_USAGE_RECORDS")

    # 验证金额合理性（总额不应该超过某个合理值，比如100万）
    total_amount = sum(usage.amount for usage in body.usages)
    if total_amount > 1000000:
        raise ValidationException("总金额超出合理范围", code="AMOUNT_TOO_LARGE")

    # 创建记录
    records = await create_first_salary_usage_records(
        db,
        current_user.id,
        recordId,
        [usage.model_dump() for usage in body.usages]
    )

    # 转换为响应格式
    response_records = []
    for record in records:
        response_records.append(FirstSalaryUsageResponse(
            id=record.id,
            salaryRecordId=record.salary_record_id,
            usageCategory=record.usage_category,
            usageSubcategory=record.usage_subcategory,
            amount=float(record.amount),
            note=record.note,
            isFirstSalary=bool(record.is_first_salary),
            createdAt=record.created_at.isoformat() if record.created_at else None
        ))

    logger.info(f"User {current_user.id} created {len(records)} first salary usage records")

    return success_response(
        data={
            "records": response_records,
            "total": len(response_records)
        },
        message="第一笔工资用途记录创建成功"
    )


@router.get("/{recordId}")
async def get_first_salary_usage(
    recordId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取第一笔工资用途记录

    根据工资记录ID获取用途详情（仅限自己的记录）
    """
    # 直接在服务层过滤用户数据，防止授权绕过
    records = await get_first_salary_usage_by_salary(db, recordId, current_user.id)

    # 转换为响应格式
    response_records = []
    for record in records:
        response_records.append(FirstSalaryUsageResponse(
            id=record.id,
            salaryRecordId=record.salary_record_id,
            usageCategory=record.usage_category,
            usageSubcategory=record.usage_subcategory,
            amount=float(record.amount),
            note=record.note,
            isFirstSalary=bool(record.is_first_salary),
            createdAt=record.created_at.isoformat() if record.created_at else None
        ))

    return success_response(
        data={
            "records": response_records,
            "total": len(response_records)
        }
    )


@router.get("/my/first-salary")
async def get_my_first_salary_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取我的第一笔工资用途记录

    返回当前用户的第一笔工资用途记录
    """
    records = await get_first_salary_usage_by_user(db, current_user.id)

    # 转换为响应格式
    response_records = []
    for record in records:
        response_records.append(FirstSalaryUsageResponse(
            id=record.id,
            salaryRecordId=record.salary_record_id,
            usageCategory=record.usage_category,
            usageSubcategory=record.usage_subcategory,
            amount=float(record.amount),
            note=record.note,
            isFirstSalary=bool(record.is_first_salary),
            createdAt=record.created_at.isoformat() if record.created_at else None
        ))

    return success_response(
        data={
            "records": response_records,
            "total": len(response_records)
        }
    )
