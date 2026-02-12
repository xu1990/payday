"""
发薪日配置 - 请求/响应模型
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.payday import PaydayConfig


class PaydayConfigBase(BaseModel):
    job_name: str = Field(..., max_length=50)
    payday: int = Field(..., ge=1, le=31)
    calendar_type: str = Field(default="solar", pattern="^(solar|lunar)$")
    estimated_salary: Optional[int] = Field(None, ge=0, description="预估工资（分）")
    is_active: int = Field(default=1, ge=0, le=1)


class PaydayConfigCreate(PaydayConfigBase):
    pass


class PaydayConfigUpdate(BaseModel):
    job_name: Optional[str] = Field(None, max_length=50)
    payday: Optional[int] = Field(None, ge=1, le=31)
    calendar_type: Optional[str] = Field(None, pattern="^(solar|lunar)$")
    estimated_salary: Optional[int] = None
    is_active: Optional[int] = Field(None, ge=0, le=1)


class PaydayConfigResponse(BaseModel):
    id: str
    user_id: str
    job_name: str
    payday: int
    calendar_type: str
    estimated_salary: Optional[int] = None
    is_active: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


def payday_to_response(m: PaydayConfig) -> dict:
    return PaydayConfigResponse.model_validate(m).model_dump()
