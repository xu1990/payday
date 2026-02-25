"""
工作记录 Schemas - 牛马日志 Module
"""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class WorkRecordBase(BaseModel):
    """工作记录基础 Schema"""
    clock_in_time: datetime = Field(..., description="打卡开始时间")
    work_type: str = Field(..., description="工作类型: regular/overtime/weekend/holiday")
    content: str = Field(..., min_length=1, max_length=2000, description="工作内容")

    clock_out_time: Optional[datetime] = Field(None, description="打卡结束时间")
    location: Optional[str] = Field(None, max_length=200, description="工作地点")
    company_name: Optional[str] = Field(None, max_length=100, description="公司名称")
    mood: Optional[str] = Field(None, max_length=20, description="心情")
    tags: Optional[List[str]] = Field(None, description="标签")
    images: Optional[List[str]] = Field(None, description="图片URL列表")

    @validator('work_type')
    def validate_work_type(cls, v):
        valid_types = ["regular", "overtime", "weekend", "holiday"]
        if v not in valid_types:
            raise ValueError(f"work_type must be one of {valid_types}")
        return v


class WorkRecordCreate(WorkRecordBase):
    """创建工作记录"""
    pass


class WorkRecordUpdate(BaseModel):
    """更新工作记录"""
    clock_out_time: Optional[datetime] = None
    content: Optional[str] = None
    mood: Optional[str] = None
    tags: Optional[List[str]] = None


class WorkRecordResponse(WorkRecordBase):
    """工作记录响应"""
    id: str
    user_id: str
    post_id: str
    clock_out_time: Optional[datetime] = None
    work_duration_minutes: Optional[int] = None
    overtime_hours: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkRecordListResponse(BaseModel):
    """工作记录列表响应"""
    total: int
    items: List[WorkRecordResponse]
    page: int
    page_size: int
