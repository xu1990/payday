"""
工资记录 - 请求/响应模型；金额 API 为元，存储为加密
"""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.salary import SalaryRecord


class SalaryRecordBase(BaseModel):
    config_id: str
    amount: float = Field(..., gt=0, description="实发金额（元）")
    payday_date: date
    salary_type: str = Field(default="normal", pattern="^(normal|bonus|allowance|other)$")
    images: Optional[List[str]] = None
    note: Optional[str] = None
    mood: str = Field(..., pattern="^(happy|relief|sad|angry|expect)$")


class SalaryRecordCreate(SalaryRecordBase):
    pass


class SalaryRecordUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    payday_date: Optional[date] = None
    salary_type: Optional[str] = Field(None, pattern="^(normal|bonus|allowance|other)$")
    images: Optional[List[str]] = None
    note: Optional[str] = None
    mood: Optional[str] = Field(None, pattern="^(happy|relief|sad|angry|expect)$")


class SalaryRecordResponse(BaseModel):
    id: str
    user_id: str
    config_id: str
    amount: float
    payday_date: date
    salary_type: str
    images: Optional[List[str]] = None
    note: Optional[str] = None
    mood: str
    risk_status: str
    created_at: datetime
    updated_at: datetime
