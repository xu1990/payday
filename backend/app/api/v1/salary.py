"""
工资记录 - list/create/get/update/delete；金额 API 为元
"""
from datetime import date
from typing import Optional

from fastapi import Depends, HTTPException, Query

from app.core.deps import get_current_user, verify_csrf_token
from app.core.database import get_db
from app.models.user import User
from app.schemas.salary import SalaryRecordCreate, SalaryRecordResponse, SalaryRecordUpdate
from app.services.salary_service import (
    create as create_record,
    delete as delete_record,
    get_by_id,
    list_by_user,
    record_to_response,
    update as update_record,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter

router = APIRouter(prefix="/salary", tags=["salary"])


@router.get("", response_model=list[SalaryRecordResponse])
async def salary_list(
    config_id: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records = await list_by_user(db, current_user.id, config_id, from_date, to_date, limit, offset)
    return [SalaryRecordResponse(**record_to_response(r)) for r in records]


@router.post("", response_model=SalaryRecordResponse)
async def salary_create(
    body: SalaryRecordCreate,
    current_user: User = Depends(get_current_user),
    _csrf: bool = Depends(verify_csrf_token),  # 添加 CSRF 保护
    db: AsyncSession = Depends(get_db),
):
    record = await create_record(db, current_user.id, body)
    return SalaryRecordResponse(**record_to_response(record))


@router.get("/{record_id}", response_model=SalaryRecordResponse)
async def salary_get(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await get_by_id(db, record_id, current_user.id)
    if not record:
        raise HTTPException(status_code=404, detail="工资记录不存在")
    return SalaryRecordResponse(**record_to_response(record))


@router.put("/{record_id}", response_model=SalaryRecordResponse)
async def salary_update(
    record_id: str,
    body: SalaryRecordUpdate,
    current_user: User = Depends(get_current_user),
    _csrf: bool = Depends(verify_csrf_token),  # 添加 CSRF 保护
    db: AsyncSession = Depends(get_db),
):
    record = await update_record(db, record_id, current_user.id, body)
    if not record:
        raise HTTPException(status_code=404, detail="工资记录不存在")
    return SalaryRecordResponse(**record_to_response(record))


@router.delete("/{record_id}", status_code=204)
async def salary_delete(
    record_id: str,
    current_user: User = Depends(get_current_user),
    _csrf: bool = Depends(verify_csrf_token),  # 添加 CSRF 保护
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_record(db, record_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="工资记录不存在")
