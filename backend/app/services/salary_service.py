"""
工资记录 - 增删改查；金额写入加密、读出解密
"""
from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salary import SalaryRecord
from app.schemas.salary import SalaryRecordCreate, SalaryRecordUpdate
from app.utils.encryption import decrypt_amount, encrypt_amount
from app.core.exceptions import NotFoundException, ValidationException


async def list_by_user(
    db: AsyncSession,
    user_id: str,
    config_id: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[SalaryRecord]:
    q = select(SalaryRecord).where(SalaryRecord.user_id == user_id)
    if config_id:
        q = q.where(SalaryRecord.config_id == config_id)
    if from_date:
        q = q.where(SalaryRecord.payday_date >= from_date)
    if to_date:
        q = q.where(SalaryRecord.payday_date <= to_date)
    q = q.order_by(SalaryRecord.payday_date.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, record_id: str, user_id: str) -> Optional[SalaryRecord]:
    result = await db.execute(
        select(SalaryRecord).where(SalaryRecord.id == record_id, SalaryRecord.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user_id: str, data: SalaryRecordCreate) -> SalaryRecord:
    try:
        amount_encrypted, salt_b64 = encrypt_amount(data.amount)
        record = SalaryRecord(
            user_id=user_id,
            config_id=data.config_id,
            amount_encrypted=amount_encrypted,
            encryption_salt=salt_b64,
            payday_date=data.payday_date,
            salary_type=data.salary_type,
            images=data.images,
            note=data.note,
            mood=data.mood,
        )
        db.add(record)
        await db.flush()
        await db.commit()
        await db.refresh(record)
        return record
    except SQLAlchemyError:
        await db.rollback()
        raise


async def update(
    db: AsyncSession, record_id: str, user_id: str, data: SalaryRecordUpdate
) -> Optional[SalaryRecord]:
    try:
        record = await get_by_id(db, record_id, user_id)
        if not record:
            raise NotFoundException("工资记录不存在")
        d = data.model_dump(exclude_unset=True)
        if "amount" in d:
            amount_encrypted, salt_b64 = encrypt_amount(d.pop("amount"))
            d["amount_encrypted"] = amount_encrypted
            d["encryption_salt"] = salt_b64
        for k, v in d.items():
            setattr(record, k, v)
        await db.flush()
        await db.commit()
        await db.refresh(record)
        return record
    except SQLAlchemyError:
        await db.rollback()
        raise


async def delete(db: AsyncSession, record_id: str, user_id: str) -> bool:
    """删除工资记录（带事务管理）"""
    try:
        record = await get_by_id(db, record_id, user_id)
        if not record:
            return False
        await db.delete(record)
        await db.commit()
        return True
    except SQLAlchemyError:
        await db.rollback()
        raise


async def get_by_id_for_admin(db: AsyncSession, record_id: str) -> Optional[SalaryRecord]:
    """管理端：按 ID 查记录（不校验 user_id）"""
    result = await db.execute(select(SalaryRecord).where(SalaryRecord.id == record_id))
    return result.scalar_one_or_none()


async def delete_for_admin(db: AsyncSession, record_id: str) -> bool:
    """管理端：删除任意工资记录（带事务管理）"""
    try:
        record = await get_by_id_for_admin(db, record_id)
        if not record:
            return False
        await db.delete(record)
        await db.commit()
        return True
    except SQLAlchemyError:
        await db.rollback()
        raise


async def update_risk_for_admin(
    db: AsyncSession, record_id: str, risk_status: str
) -> Optional[SalaryRecord]:
    """管理端：人工审核工资记录（通过/拒绝）（带事务管理）"""
    from datetime import datetime

    try:
        record = await get_by_id_for_admin(db, record_id)
        if not record:
            raise NotFoundException("工资记录不存在")
        if risk_status not in ("approved", "rejected"):
            raise ValidationException("risk_status 必须是 approved 或 rejected")
        record.risk_status = risk_status
        record.risk_check_time = datetime.utcnow()
        await db.commit()
        await db.refresh(record)
        return record
    except SQLAlchemyError:
        await db.rollback()
        raise


async def list_all_for_admin(
    db: AsyncSession,
    user_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple:
    """管理端：工资记录分页，返回 (list of response dict, total_count)；金额已解密"""
    from sqlalchemy import func

    count_q = select(func.count()).select_from(SalaryRecord)
    if user_id:
        count_q = count_q.where(SalaryRecord.user_id == user_id)
    total_result = await db.execute(count_q)
    total_count = total_result.scalar() or 0
    q = select(SalaryRecord).order_by(
        SalaryRecord.payday_date.desc(), SalaryRecord.created_at.desc()
    ).limit(limit).offset(offset)
    if user_id:
        q = q.where(SalaryRecord.user_id == user_id)
    result = await db.execute(q)
    records = list(result.scalars().all())
    items = [record_to_response(r) for r in records]
    return items, total_count


def record_to_response(record: SalaryRecord) -> dict:
    """将 ORM 转为响应 dict，金额解密为元"""
    amount = decrypt_amount(record.amount_encrypted, record.encryption_salt)
    return {
        "id": record.id,
        "user_id": record.user_id,
        "config_id": record.config_id,
        "amount": amount,
        "payday_date": record.payday_date,
        "salary_type": record.salary_type,
        "images": record.images,
        "note": record.note,
        "mood": record.mood,
        "risk_status": record.risk_status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
