"""Expense Record Service"""
from datetime import date
from decimal import Decimal
from typing import List

from app.models.expense_record import ExpenseRecord
from app.schemas.expense_record import ExpenseRecordCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_expense_records(
    db: AsyncSession,
    user_id: str,
    salary_record_id: str,
    expenses: List[dict]
) -> List[ExpenseRecord]:
    """创建支出记录"""
    created_records = []
    for exp in expenses:
        record = ExpenseRecord(
            user_id=user_id,
            salary_record_id=salary_record_id,
            expense_date=exp["expenseDate"],
            category=exp["category"],
            subcategory=exp.get("subcategory"),
            amount=Decimal(str(exp["amount"])),
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
    """获取工资记录的支出"""
    stmt = (
        select(ExpenseRecord)
        .where(ExpenseRecord.salary_record_id == salary_record_id)
        .order_by(ExpenseRecord.expense_date)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    # 转换为字典
    expense_list = []
    for record in records:
        expense_list.append({
            "id": record.id,
            "salaryRecordId": record.salary_record_id,
            "expenseDate": record.expense_date.isoformat() if record.expense_date else None,
            "category": record.category,
            "subcategory": record.subcategory,
            "amount": float(record.amount),
            "note": record.note,
            "createdAt": record.created_at.isoformat() if record.created_at else None,
        })

    return expense_list


async def get_monthly_expense_summary(
    db: AsyncSession,
    user_id: str,
    year: int,
    month: int
) -> dict:
    """获取月度支出汇总"""
    from app.models.expense_record import ExpenseRecord
    from sqlalchemy import func

    stmt = (
        select(ExpenseRecord)
        .where(ExpenseRecord.user_id == user_id)
        .where(func.extract('year', ExpenseRecord.expense_date) == year)
        .where(func.extract('month', ExpenseRecord.expense_date) == month)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    # 按分类汇总
    summary = {}
    for record in records:
        category = record.category
        summary[category] = summary.get(category, 0) + float(record.amount)

    return summary
