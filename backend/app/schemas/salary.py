"""
工资记录 - 请求/响应模型；金额 API 为明文（元），数据库存储为加密

安全流程：
1. 用户输入明文金额
2. API 通过 SalaryRecordCreate 接收明文
3. Service 层使用 encrypt_amount() 加密后存储为 amount_encrypted
4. 读取时使用 decrypt_amount() 解密后通过 SalaryRecordResponse 返回明文
"""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.salary import SalaryRecord


class SalaryRecordBase(BaseModel):
    config_id: str
    amount: float = Field(
        ...,
        gt=0,
        le=10000000,  # 最高1000万元
        description="实发金额（元）- 明文接收，将在 service 层加密"
    )
    payday_date: date
    salary_type: str = Field(default="normal", pattern="^(normal|bonus|allowance|other)$")
    images: Optional[List[str]] = None
    note: Optional[str] = Field(None, max_length=500)
    mood: str = Field(..., pattern="^(happy|relief|sad|angry|expect)$")

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """验证金额格式：最多2位小数"""
        # 转换为字符串检查小数位数
        amount_str = str(v)
        if '.' in amount_str:
            decimal_places = len(amount_str.split('.')[1])
            if decimal_places > 2:
                raise ValueError('金额最多保留2位小数')
        # 四舍五入到2位小数
        return round(v, 2)

    @field_validator('note')
    @classmethod
    def validate_note(cls, v: Optional[str]) -> Optional[str]:
        """验证备注内容"""
        if v is not None:
            # 去除首尾空白
            v = v.strip()
            if not v:
                return None
        return v


class SalaryRecordCreate(SalaryRecordBase):
    """
    创建工资记录请求
    注意：amount 字段为明文，由 salary_service.create() 使用 encrypt_amount() 加密后存储
    """


class SalaryRecordUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    payday_date: Optional[date] = None
    salary_type: Optional[str] = Field(None, pattern="^(normal|bonus|allowance|other)$")
    images: Optional[List[str]] = None
    note: Optional[str] = None
    mood: Optional[str] = Field(None, pattern="^(happy|relief|sad|angry|expect)$")


class SalaryRecordResponse(BaseModel):
    """
    工资记录响应
    注意：amount 字段已由 decrypt_amount() 解密，可安全返回
    """
    id: str
    user_id: str
    config_id: str
    amount: float  # 已解密的明文金额
    payday_date: date
    salary_type: str
    images: Optional[List[str]] = None
    note: Optional[str] = None
    mood: str
    risk_status: str
    created_at: datetime
    updated_at: datetime
