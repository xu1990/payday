"""
First Salary Usage Schemas - 第一笔工资用途相关数据验证
"""
from pydantic import BaseModel, Field
from typing import Optional


class FirstSalaryUsageCreate(BaseModel):
    """创建第一笔工资用途记录"""
    usageCategory: str = Field(..., description="用途分类", min_length=1, max_length=50)
    usageSubcategory: Optional[str] = Field(None, description="子分类", max_length=50)
    amount: float = Field(..., gt=0, description="用途金额")
    note: Optional[str] = Field(None, description="备注")


class FirstSalaryUsageResponse(BaseModel):
    """第一笔工资用途记录响应"""
    id: str
    salaryRecordId: str
    usageCategory: str
    usageSubcategory: Optional[str] = None
    amount: float
    note: Optional[str] = None
    isFirstSalary: bool
    createdAt: Optional[str] = None

    class Config:
        from_attributes = True


class FirstSalaryUsageListCreate(BaseModel):
    """批量创建第一笔工资用途记录"""
    usages: list[FirstSalaryUsageCreate]

    class Config:
        json_schema_extra = {
            "example": {
                "usages": [
                    {
                        "usageCategory": "存起来",
                        "usageSubcategory": "银行存款",
                        "amount": 2000.0,
                        "note": "第一笔工资存银行"
                    },
                    {
                        "usageCategory": "交家里",
                        "amount": 1000.0
                    }
                ]
            }
        }
