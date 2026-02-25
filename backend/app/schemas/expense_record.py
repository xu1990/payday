"""Expense Record Schemas - 支出记录数据验证"""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ExpenseRecordCreate(BaseModel):
    """创建支出记录请求"""
    expenseDate: date = Field(..., description="支出日期")
    category: str = Field(..., min_length=1, max_length=50, description="支出分类")
    subcategory: Optional[str] = Field(None, max_length=50, description="子分类")
    amount: float = Field(..., gt=0, description="支出金额")
    note: Optional[str] = Field(None, description="备注")


class ExpenseRecordResponse(BaseModel):
    """支出记录响应"""
    id: str
    salaryRecordId: str
    expenseDate: date
    category: str
    subcategory: Optional[str] = None
    amount: float
    note: Optional[str] = None
    createdAt: datetime

    model_config = {"from_attributes": True}


class ExpenseListCreate(BaseModel):
    """批量创建支出记录请求"""
    expenses: List[ExpenseRecordCreate] = Field(..., min_items=1, max_items=50, description="支出记录列表")
