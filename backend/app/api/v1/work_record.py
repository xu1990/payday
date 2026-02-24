"""
工作记录 API - 牛马日志 Module
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ValidationException, success_response
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.work_record import (
    WorkRecordCreate,
    WorkRecordResponse,
    WorkRecordListResponse
)
from app.services.work_record_service import WorkRecordService

router = APIRouter(prefix="/work-logs", tags=["work-logs"])


@router.post("", response_model=dict)
async def create_work_log(
    work_data: WorkRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建工作记录（打卡上班）

    自动创建关联的 Post，类型为 work
    """
    service = WorkRecordService(db)

    work_record = await service.create_work_record(
        user_id=current_user.id,
        work_data=work_data
    )

    return success_response(
        data=WorkRecordResponse.model_validate(work_record).model_dump(mode='json'),
        message="打卡成功"
    )


@router.get("", response_model=dict)
async def list_work_logs(
    date_from: Optional[str] = Query(None, description="起始日期 ISO格式"),
    date_to: Optional[str] = Query(None, description="结束日期 ISO格式"),
    work_type: Optional[str] = Query(None, description="工作类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户的工作记录列表（分页）
    """
    service = WorkRecordService(db)

    # Parse date filters if provided
    start_date = datetime.fromisoformat(date_from) if date_from else None
    end_date = datetime.fromisoformat(date_to) if date_to else None

    work_records = await service.get_user_work_records(
        user_id=current_user.id,
        date_from=start_date,
        date_to=end_date,
        work_type=work_type,
        page=page,
        page_size=page_size
    )

    items = [WorkRecordResponse.model_validate(r).model_dump(mode='json') for r in work_records]

    return success_response(
        data={
            "items": items,
            "total": len(items),
            "page": page,
            "page_size": page_size
        },
        message="获取工作记录列表成功"
    )


@router.get("/{work_log_id}", response_model=dict)
async def get_work_log_detail(
    work_log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取工作记录详情
    """
    service = WorkRecordService(db)

    # Get user's work records and filter by ID
    work_records = await service.get_user_work_records(
        user_id=current_user.id,
        page=1,
        page_size=1000  # Get all to find the specific one
    )

    work_record = next((r for r in work_records if r.id == work_log_id), None)

    if not work_record:
        raise NotFoundException("工作记录不存在")

    return success_response(
        data=WorkRecordResponse.model_validate(work_record).model_dump(mode='json'),
        message="获取工作记录详情成功"
    )


@router.put("/{work_log_id}/clock-out", response_model=dict)
async def clock_out(
    work_log_id: str,
    clock_out_time: Optional[str] = Query(None, description="打卡下班时间 ISO格式，默认为当前时间"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    打卡下班

    更新工作记录的下班时间并计算工作时长
    """
    service = WorkRecordService(db)

    # Use current time if not provided
    out_time = datetime.fromisoformat(clock_out_time) if clock_out_time else datetime.utcnow()

    try:
        work_record = await service.clock_out(
            work_record_id=work_log_id,
            clock_out_time=out_time
        )
    except NotFoundException:
        raise NotFoundException("工作记录不存在")
    except ValidationException as e:
        raise ValidationException(e.message)

    return success_response(
        data=WorkRecordResponse.model_validate(work_record).model_dump(mode='json'),
        message="打卡下班成功"
    )
