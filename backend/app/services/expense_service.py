"""Expense Record Service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import date

from app.models.expense_record import ExpenseRecord
from app.schemas.expense_record import ExpenseRecordCreate


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
            amount=exp["amount"],
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
) -> List[ExpenseRecord]:
    """获取工资记录的支出"""
    stmt = (
        select(ExpenseRecord)
        .where(ExpenseRecord.salary_record_id == salary_record_id)
        .order_by(ExpenseRecord.expense_date)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_monthly_expense_summary(
    db: AsyncSession,
    user_id: str,
    year: int,
    month: int
) -> dict:
    """获取月度支出汇总"""
    from sqlalchemy import func
    from app.models.expense_record import ExpenseRecord
    
    stmt = (
        select(
            ExpenseRecord.category,
            func.sum(ExpenseRecord.amount).label('total')
        )
        .where(ExpenseRecord.user_id == user_id)
        .where(func.extract('year', ExpenseRecord.expense_date) == year)
        .where(func.extract('month', ExpenseRecord.expense_date) == month)
        .group_by(ExpenseRecord.category)
    )
    result = await db.execute(stmt)
    return {row.category: float(row.total) for row in result}
