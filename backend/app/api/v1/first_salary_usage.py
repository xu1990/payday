"""
第一笔工资用途 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, rate_limit_general
from app.models.user import User
from app.models.first_salary_usage import FirstSalaryUsage
from app.schemas.first_salary_usage import (
    FirstSalaryUsageCreate,
    FirstSalaryUsageResponse,
    FirstSalaryUsageUpdate,
    FirstSalaryUsageListResponse,
)
from app.services.first_salary_usage_service import (
    create_first_salary_usage,
    get_first_salary_usage,
    update_first_salary_usage,
    delete_first_salary_usage,
    list_first_salary_usages,
    get_usage_statistics_by_category,
    _decrypt_with_salt,
)
from app.core.exceptions import success_response

router = APIRouter(prefix="/first-salary-usage", tags=["第一笔工资用途"])


@router.post("", dependencies=[Depends(rate_limit_general)], response_model=dict, summary="创建第一笔工资用途记录")
async def create_usage(
    usage_data: FirstSalaryUsageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    创建第一笔工资用途记录

    Args:
        usage_data: 用途记录数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        创建的用途记录
    """
    record = await create_first_salary_usage(db, current_user.id, usage_data)
    response_data = _convert_to_response(record)
    return success_response(
        data=response_data.model_dump(mode='json'),
        message="创建第一笔工资用途记录成功"
    )


@router.get("/statistics/by-category", summary="按分类统计用途金额")
async def get_statistics(
    salary_record_id: Optional[str] = Query(None, description="薪资记录ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    按分类统计用途金额

    Args:
        salary_record_id: 筛选薪资记录ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        统计结果
    """
    stats = await get_usage_statistics_by_category(db, current_user.id, salary_record_id)
    return success_response(
        data={"statistics": stats},
        message="获取统计信息成功"
    )


@router.get("/{usage_id}", response_model=dict, summary="获取第一笔工资用途记录")
async def get_usage(
    usage_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取第一笔工资用途记录

    Args:
        usage_id: 用途记录ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        用途记录
    """
    record = await get_first_salary_usage(db, usage_id, current_user.id)
    response_data = _convert_to_response(record)
    return success_response(
        data=response_data.model_dump(mode='json'),
        message="获取第一笔工资用途记录成功"
    )


@router.put("/{usage_id}", response_model=dict, summary="更新第一笔工资用途记录")
async def update_usage(
    usage_id: str,
    update_data: FirstSalaryUsageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    更新第一笔工资用途记录

    Args:
        usage_id: 用途记录ID
        update_data: 更新数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        更新后的用途记录
    """
    record = await update_first_salary_usage(db, usage_id, current_user.id, update_data)
    response_data = _convert_to_response(record)
    return success_response(
        data=response_data.model_dump(mode='json'),
        message="更新第一笔工资用途记录成功"
    )


@router.delete("/{usage_id}", summary="删除第一笔工资用途记录")
async def delete_usage(
    usage_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    删除第一笔工资用途记录

    Args:
        usage_id: 用途记录ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        删除结果
    """
    await delete_first_salary_usage(db, usage_id, current_user.id)
    return success_response(message="删除第一笔工资用途记录成功")


@router.get("", response_model=dict, summary="获取第一笔工资用途记录列表")
async def list_usages(
    salary_record_id: Optional[str] = Query(None, description="薪资记录ID"),
    usage_category: Optional[str] = Query(None, description="用途分类"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取第一笔工资用途记录列表

    Args:
        salary_record_id: 筛选薪资记录ID
        usage_category: 筛选用途分类
        skip: 跳过记录数
        limit: 返回记录数
        current_user: 当前用户
        db: 数据库会话

    Returns:
        记录列表
    """
    usages, total = await list_first_salary_usages(
        db, current_user.id, salary_record_id, usage_category, skip, limit
    )
    items = [_convert_to_response(u).model_dump(mode='json') for u in usages]
    return success_response(
        data={"total": total, "items": items},
        message="获取第一笔工资用途记录列表成功"
    )


def _convert_to_response(record: FirstSalaryUsage) -> FirstSalaryUsageResponse:
    """转换数据库记录为响应格式"""
    # Decrypt amount for response
    decrypted_amount = _decrypt_with_salt(record.amount)

    return FirstSalaryUsageResponse(
        id=record.id,
        salary_record_id=record.salary_record_id,
        usage_category=record.usage_category,
        usage_subcategory=record.usage_subcategory,
        amount=decrypted_amount,
        note=record.note,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
