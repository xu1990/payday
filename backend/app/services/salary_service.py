"""
工资记录 - 增删改查；金额写入加密、读出解密
使用统一的 transactional context manager 进行事务管理
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
from app.core.database import transactional


def record_to_response(record: SalaryRecord) -> dict:
    """
    将数据库记录转换为响应字典（解密金额）

    Args:
        record: SalaryRecord 数据库模型实例

    Returns:
        dict: 符合 SalaryRecordResponse schema 的字典
    """
    return {
        "id": record.id,
        "user_id": record.user_id,
        "config_id": record.config_id,
        "amount": decrypt_amount(record.amount_encrypted, record.encryption_salt),
        "payday_date": record.payday_date,
        "salary_type": record.salary_type,
        "images": record.images,
        "note": record.note,
        "mood": record.mood,
        "risk_status": record.risk_status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


async def list_by_user(
    db: AsyncSession,
    user_id: str,
    config_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[SalaryRecord]:
    """获取用户工资记录列表"""
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
    """获取单条工资记录"""
    result = await db.execute(
        select(SalaryRecord).where(
            SalaryRecord.id == record_id, SalaryRecord.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user_id: str, data: SalaryRecordCreate) -> SalaryRecord:
    """创建工资记录（使用事务管理器）"""
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

        async with transactional(db) as session:
            session.add(record)
            # 自动提交或异常时回滚
            await session.flush(record)
            return record
    except SQLAlchemyError:
        raise


async def update(
    db: AsyncSession, record_id: str, user_id: str, data: SalaryRecordUpdate
) -> Optional[SalaryRecord]:
    """更新工资记录（使用事务管理器）"""
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

        async with transactional(db) as session:
            # session.merge 会自动处理更新
            session.merge(record)
            # 自动提交或异常时回滚
            await session.flush()
            return record
    except SQLAlchemyError:
        raise


async def delete(db: AsyncSession, record_id: str, user_id: str) -> bool:
    """删除工资记录（使用事务管理器）"""
    try:
        record = await get_by_id(db, record_id, user_id)
        if not record:
            return False

        async with transactional(db) as session:
            await session.delete(record)
            # 自动提交或异常时回滚
            return True
    except SQLAlchemyError:
        raise


async def get_by_id_for_admin(db: AsyncSession, record_id: str) -> Optional[SalaryRecord]:
    """管理端：按 ID 查记录（不校验 user_id）"""
    result = await db.execute(select(SalaryRecord).where(SalaryRecord.id == record_id))
    return result.scalar_one_or_none()


async def delete_for_admin(db: AsyncSession, record_id: str) -> bool:
    """管理端：删除任意工资记录（使用事务管理器）"""
    try:
        record = await get_by_id_for_admin(db, record_id)
        if not record:
            return False

        async with transactional(db) as session:
            await session.delete(record)
            # 自动提交或异常时回滚
            return True
    except SQLAlchemyError:
        raise


async def update_risk_for_admin(
    db: AsyncSession, record_id: str, risk_status: str
) -> Optional[SalaryRecord]:
    """管理端：人工审核工资记录（通过/拒绝）（使用事务管理器）"""
    from datetime import datetime

    try:
        record = await get_by_id_for_admin(db, record_id)
        if not record:
            raise NotFoundException("工资记录不存在")
        if risk_status not in ("approved", "rejected"):
            raise ValidationException("risk_status 必须是 approved 或 rejected")
        record.risk_status = risk_status
        record.risk_check_time = datetime.utcnow()

        async with transactional(db) as session:
            session.merge(record)
            # 自动提交或异常时回滚
            await session.flush()
            return record
    except SQLAlchemyError:
        raise
