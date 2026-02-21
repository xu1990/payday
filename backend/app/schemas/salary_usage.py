"""
薪资使用记录 Schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SalaryUsageBase(BaseModel):
    """薪资使用记录基础 Schema"""
    usage_type: str = Field(..., description="使用类型: housing/food/transport/shopping/entertainment/medical/education/other")
    amount: float = Field(..., gt=0, description="使用金额（明文，前端传入）")
    usage_date: datetime = Field(..., description="使用日期")
    description: Optional[str] = Field(None, max_length=500, description="备注说明")


class SalaryUsageCreate(SalaryUsageBase):
    """创建薪资使用记录"""
    salary_record_id: str = Field(..., description="薪资记录ID")


class SalaryUsageUpdate(BaseModel):
    """更新薪资使用记录"""
    usage_type: Optional[str] = Field(None, description="使用类型")
    amount: Optional[float] = Field(None, gt=0, description="使用金额")
    usage_date: Optional[datetime] = Field(None, description="使用日期")
    description: Optional[str] = Field(None, max_length=500, description="备注说明")


class SalaryUsageInDB(SalaryUsageBase):
    """数据库中的薪资使用记录（包含ID和时间戳）"""
    id: str
    user_id: str
    salary_record_id: str
    amount: str  # 加密后的金额
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalaryUsageResponse(SalaryUsageBase):
    """薪资使用记录响应（返回给前端）"""
    id: str
    salary_record_id: str
    amount: float  # 解密后的金额
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalaryUsageListResponse(BaseModel):
    """薪资使用记录列表响应"""
    total: int = Field(..., description="总记录数")
    items: list[SalaryUsageResponse] = Field(..., description="记录列表")
