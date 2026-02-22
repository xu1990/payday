"""Expense API - 支出记录接口"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, rate_limit_general
from app.core.exceptions import success_response
from app.models.user import User
from app.schemas.expense_record import ExpenseListCreate, ExpenseRecordResponse
from app.services.expense_service import create_expense_records, get_expenses_by_salary

router = APIRouter(prefix="/salary", tags=["expenses"])

@router.post("/{recordId}/expenses", dependencies=[Depends(rate_limit_general)])
async def create_expenses(recordId: str, body: ExpenseListCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    records = await create_expense_records(db, current_user.id, recordId, [exp.model_dump() for exp in body.expenses])
    response = [ExpenseRecordResponse(id=r.id, salaryRecordId=r.salary_record_id, expenseDate=r.expense_date, category=r.category, subcategory=r.subcategory, amount=float(r.amount), note=r.note, createdAt=r.created_at) for r in records]
    return success_response(data={"records": response, "total": len(response)}, message="支出记录创建成功")

@router.get("/{recordId}/expenses")
async def get_expenses(recordId: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    records = await get_expenses_by_salary(db, recordId)
    response = [ExpenseRecordResponse(id=r.id, salaryRecordId=r.salary_record_id, expenseDate=r.expense_date, category=r.category, subcategory=r.subcategory, amount=float(r.amount), note=r.note, createdAt=r.created_at) for r in records]
    return success_response(data={"records": response, "total": len(response)})
