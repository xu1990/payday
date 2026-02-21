"""
薪资使用记录 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.salary_usage import (
    SalaryUsageCreate,
    SalaryUsageResponse,
    SalaryUsageUpdate,
    SalaryUsageListResponse,
)
from app.services.salary_usage_service import (
    create_salary_usage,
    get_salary_usage,
    update_salary_usage,
    delete_salary_usage,
    list_salary_usages,
    get_usage_statistics_by_type,
    _decrypt_with_salt,
)
from app.models.salary_usage import SalaryUsageRecord
from app.core.exceptions import success_response

router = APIRouter(prefix="/salary-usage", tags=["薪资使用记录"])


@router.post("", response_model=dict, summary="创建薪资使用记录")
async def create_usage(
    usage_data: SalaryUsageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    创建薪资使用记录

    Args:
        usage_data: 使用记录数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        创建的使用记录
    """
    record = await create_salary_usage(db, current_user.id, usage_data)
    response_data = _convert_to_response(record)
    return success_response(
        data=response_data.model_dump(mode='json'),
        message="创建薪资使用记录成功"
    )


@router.get("/statistics/by-type", summary="按类型统计使用金额")
async def get_statistics(
    salary_record_id: Optional[str] = Query(None, description="薪资记录ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    按类型统计使用金额

    Args:
        salary_record_id: 筛选薪资记录ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        统计结果
    """
    stats = await get_usage_statistics_by_type(db, current_user.id, salary_record_id)
    return success_response(
        data={"statistics": stats},
        message="获取统计信息成功"
    )


@router.get("/{usage_id}", response_model=dict, summary="获取薪资使用记录")
async def get_usage(
    usage_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取薪资使用记录

    Args:
        usage_id: 使用记录ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        使用记录
    """
    record = await get_salary_usage(db, usage_id, current_user.id)
    response_data = _convert_to_response(record)
    return success_response(
        data=response_data.model_dump(mode='json'),
        message="获取薪资使用记录成功"
    )


@router.put("/{usage_id}", response_model=dict, summary="更新薪资使用记录")
async def update_usage(
    usage_id: str,
    update_data: SalaryUsageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    更新薪资使用记录

    Args:
        usage_id: 使用记录ID
        update_data: 更新数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        更新后的使用记录
    """
    record = await update_salary_usage(db, usage_id, current_user.id, update_data)
    response_data = _convert_to_response(record)
    return success_response(
        data=response_data.model_dump(mode='json'),
        message="更新薪资使用记录成功"
    )


@router.delete("/{usage_id}", summary="删除薪资使用记录")
async def delete_usage(
    usage_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    删除薪资使用记录

    Args:
        usage_id: 使用记录ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        删除结果
    """
    await delete_salary_usage(db, usage_id, current_user.id)
    return success_response(message="删除薪资使用记录成功")


@router.get("", response_model=dict, summary="获取薪资使用记录列表")
async def list_usages(
    salary_record_id: Optional[str] = Query(None, description="薪资记录ID"),
    usage_type: Optional[str] = Query(None, description="使用类型"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取薪资使用记录列表

    Args:
        salary_record_id: 筛选薪资记录ID
        usage_type: 筛选使用类型
        skip: 跳过记录数
        limit: 返回记录数
        current_user: 当前用户
        db: 数据库会话

    Returns:
        记录列表
    """
    usages, total = await list_salary_usages(
        db, current_user.id, salary_record_id, usage_type, skip, limit
    )
    items = [_convert_to_response(u).model_dump(mode='json') for u in usages]
    return success_response(
        data={"total": total, "items": items},
        message="获取薪资使用记录列表成功"
    )


def _convert_to_response(record: SalaryUsageRecord) -> SalaryUsageResponse:
    """转换数据库记录为响应格式"""
    # Decrypt amount for response
    decrypted_amount = _decrypt_with_salt(record.amount)

    return SalaryUsageResponse(
        id=record.id,
        salary_record_id=record.salary_record_id,
        usage_type=record.usage_type,
        amount=decrypted_amount,
        usage_date=record.usage_date,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
