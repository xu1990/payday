"""Savings Goal Schemas - 存款目标数据验证（Sprint 4.4）"""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SavingsGoalCreate(BaseModel):
    """创建存款目标请求"""
    title: str = Field(..., min_length=1, max_length=100, description="目标标题")
    description: Optional[str] = Field(None, description="目标描述")
    target_amount: float = Field(..., gt=0, description="目标金额")
    current_amount: float = Field(0, ge=0, description="当前已存金额")
    deadline: Optional[date] = Field(None, description="目标截止日期")
    start_date: Optional[date] = Field(None, description="目标开始日期")
    category: Optional[str] = Field(None, max_length=50, description="目标分类")
    icon: Optional[str] = Field(None, max_length=50, description="图标")


class SavingsGoalUpdate(BaseModel):
    """更新存款目标请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    current_amount: Optional[float] = Field(None, ge=0)
    deadline: Optional[date] = None
    start_date: Optional[date] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|cancelled|paused)$")
    category: Optional[str] = Field(None, max_length=50)
    icon: Optional[str] = Field(None, max_length=50)


class SavingsGoalResponse(BaseModel):
    """存款目标响应"""
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    target_amount: float
    current_amount: float
    deadline: Optional[date] = None
    start_date: Optional[date] = None
    status: str
    category: Optional[str] = None
    icon: Optional[str] = None
    progress_percentage: float = 0  # 进度百分比
    remaining_amount: float = 0  # 剩余金额
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SavingsGoalDeposit(BaseModel):
    """存款操作请求"""
    amount: float = Field(..., gt=0, description="存款金额")
    note: Optional[str] = Field(None, description="备注")
