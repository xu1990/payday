"""
第一笔工资用途 Schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FirstSalaryUsageBase(BaseModel):
    """第一笔工资用途基础 Schema"""
    usage_category: str = Field(..., min_length=1, max_length=50, description="用途分类")
    usage_subcategory: Optional[str] = Field(None, max_length=50, description="子分类")
    amount: float = Field(..., gt=0, description="用途金额（明文，前端传入）")
    note: Optional[str] = Field(None, max_length=500, description="备注")


class FirstSalaryUsageCreate(FirstSalaryUsageBase):
    """创建第一笔工资用途"""
    salary_record_id: str = Field(..., description="薪资记录ID")


class FirstSalaryUsageUpdate(BaseModel):
    """更新第一笔工资用途"""
    usage_category: Optional[str] = Field(None, min_length=1, max_length=50, description="用途分类")
    usage_subcategory: Optional[str] = Field(None, max_length=50, description="子分类")
    amount: Optional[float] = Field(None, gt=0, description="用途金额")
    note: Optional[str] = Field(None, max_length=500, description="备注")


class FirstSalaryUsageInDB(FirstSalaryUsageBase):
    """数据库中的第一笔工资用途（包含ID和时间戳）"""
    id: str
    user_id: str
    salary_record_id: str
    amount: str  # 加密后的金额
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FirstSalaryUsageResponse(FirstSalaryUsageBase):
    """第一笔工资用途响应（返回给前端）"""
    id: str
    salary_record_id: str
    amount: float  # 解密后的金额
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FirstSalaryUsageListResponse(BaseModel):
    """第一笔工资用途列表响应"""
    total: int = Field(..., description="总记录数")
    items: list[FirstSalaryUsageResponse] = Field(..., description="记录列表")
