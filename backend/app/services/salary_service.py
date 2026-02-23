"""
工资记录 - 增删改查；金额写入加密、读出解密
使用统一的 transactional context manager 进行事务管理
"""
from datetime import date, datetime
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
        # Sprint 4.3 fields
        "is_arrears": record.is_arrears or 0,
        "arrears_amount": float(record.arrears_amount) if record.arrears_amount else None,
        "mood_note": record.mood_note,
        "mood_tags": record.mood_tags,
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
    from app.services.ability_points_service import trigger_event

    try:
        # 先检查是否是用户的第一次工资记录
        existing_result = await db.execute(
            select(SalaryRecord).where(SalaryRecord.user_id == user_id)
        )
        existing_count = len(existing_result.scalars().all())
        is_first = existing_count == 0

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
            # Sprint 4.3 fields
            is_arrears=data.is_arrears if hasattr(data, 'is_arrears') else 0,
            arrears_amount=data.arrears_amount if hasattr(data, 'arrears_amount') else None,
            mood_note=data.mood_note if hasattr(data, 'mood_note') else None,
            mood_tags=data.mood_tags if hasattr(data, 'mood_tags') else None,
        )

        async with transactional(db) as session:
            session.add(record)
            # 自动提交或异常时回滚
            await session.flush()

        # 发放积分（事务提交后）
        if is_first:  # 这是第一笔工资
            await trigger_event(
                db, user_id, "first_salary",
                reference_id=str(record.id),
                reference_type="salary",
                description="第一笔工资"
            )

        await trigger_event(
            db, user_id, "salary_record",
            reference_id=str(record.id),
            reference_type="salary",
            description="记录工资"
        )

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


async def list_all_for_admin(
    db: AsyncSession,
    user_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[List[dict], int]:
    """
    管理员查询所有工资记录（分页）

    Args:
        db: 数据库会话
        user_id: 可选的用户ID过滤
        limit: 每页数量
        offset: 偏移量

    Returns:
        (工资记录列表, 总数)
    """
    query = select(SalaryRecord).order_by(SalaryRecord.created_at.desc())

    # Apply user_id filter if provided
    if user_id:
        query = query.where(SalaryRecord.user_id == user_id)

    # Get paginated results
    result = await db.execute(
        query.limit(limit).offset(offset)
    )
    records = result.scalars().all()

    # Get total count (respecting the user_id filter)
    count_query = select(SalaryRecord.id)
    if user_id:
        count_query = count_query.where(SalaryRecord.user_id == user_id)

    count_result = await db.execute(count_query)
    total = len(count_result.all())

    return [record_to_response(record) for record in records], total
