"""
打卡 - 请求/响应模型；Sprint 3.3
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class CheckInCreate(BaseModel):
    """打卡请求"""
    check_date: date = Field(..., description="打卡日期")
    note: Optional[str] = Field(None, max_length=500, description="打卡备注")


class CheckInItem(BaseModel):
    """打卡日历项"""
    date: str
    checked: bool = True
    note: Optional[str] = None

    class Config:
        from_attributes = True


class CheckInCalendarResponse(BaseModel):
    """打卡日历响应"""
    items: list[CheckInItem]


class CheckInStatsResponse(BaseModel):
    """打卡统计响应"""
    total_days: int
    this_month: int
    current_streak: int
