"""Expense Record Service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import date

from app.models.expense_record import ExpenseRecord
from app.schemas.expense_record import ExpenseRecordCreate
from app.utils.encryption import encrypt_amount, decrypt_amount


async def create_expense_records(
    db: AsyncSession,
    user_id: str,
    salary_record_id: str,
    expenses: List[dict]
) -> List[ExpenseRecord]:
    """创建支出记录"""
    created_records = []
    for exp in expenses:
        # 加密金额
        encrypted_amount, salt = encrypt_amount(exp["amount"])

        record = ExpenseRecord(
            user_id=user_id,
            salary_record_id=salary_record_id,
            expense_date=exp["expenseDate"],
            category=exp["category"],
            subcategory=exp.get("subcategory"),
            amount=encrypted_amount,
            amount_salt=salt,
            note=exp.get("note")
        )
        db.add(record)
        created_records.append(record)

    await db.commit()
    for record in created_records:
        await db.refresh(record)
    return created_records


async def get_expenses_by_salary(
    db: AsyncSession,
    salary_record_id: str
) -> List[dict]:
    """获取工资记录的支出（解密金额）"""
    stmt = (
        select(ExpenseRecord)
        .where(ExpenseRecord.salary_record_id == salary_record_id)
        .order_by(ExpenseRecord.expense_date)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    # 解密金额
    decrypted_records = []
    for record in records:
        decrypted_amount = decrypt_amount(str(record.amount), record.amount_salt)
        decrypted_records.append({
            "id": record.id,
            "salaryRecordId": record.salary_record_id,
            "expenseDate": record.expense_date.isoformat() if record.expense_date else None,
            "category": record.category,
            "subcategory": record.subcategory,
            "amount": decrypted_amount,
            "note": record.note,
            "createdAt": record.created_at.isoformat() if record.created_at else None,
        })

    return decrypted_records


async def get_monthly_expense_summary(
    db: AsyncSession,
    user_id: str,
    year: int,
    month: int
) -> dict:
    """获取月度支出汇总（解密金额）"""
    from sqlalchemy import func
    from app.models.expense_record import ExpenseRecord

    stmt = (
        select(ExpenseRecord)
        .where(ExpenseRecord.user_id == user_id)
        .where(func.extract('year', ExpenseRecord.expense_date) == year)
        .where(func.extract('month', ExpenseRecord.expense_date) == month)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    # 解密并按分类汇总
    summary = {}
    for record in records:
        decrypted_amount = decrypt_amount(str(record.amount), record.amount_salt)
        category = record.category
        summary[category] = summary.get(category, 0) + float(decrypted_amount)

    return summary
