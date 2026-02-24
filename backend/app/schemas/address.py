"""
地址相关的Pydantic模型 - Address Schemas

包含用户地址的请求和响应模型：
- UserAddressResponse - 地址响应
- UserAddressUpdate - 更新地址请求
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UserAddressResponse(BaseModel):
    """用户地址响应"""
    id: str
    user_id: str
    province_code: str
    province_name: str
    city_code: str
    city_name: str
    district_code: str
    district_name: str
    detailed_address: str
    postal_code: Optional[str] = None
    contact_name: str
    contact_phone: str
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAddressUpdate(BaseModel):
    """更新地址请求"""
    province_code: Optional[str] = Field(None, min_length=1, max_length=20, description="省份代码")
    province_name: Optional[str] = Field(None, min_length=1, max_length=50, description="省份名称")
    city_code: Optional[str] = Field(None, min_length=1, max_length=20, description="城市代码")
    city_name: Optional[str] = Field(None, min_length=1, max_length=50, description="城市名称")
    district_code: Optional[str] = Field(None, min_length=1, max_length=20, description="区县代码")
    district_name: Optional[str] = Field(None, min_length=1, max_length=50, description="区县名称")
    detailed_address: Optional[str] = Field(None, min_length=1, max_length=200, description="详细地址")
    postal_code: Optional[str] = Field(None, max_length=10, description="邮政编码")
    contact_name: Optional[str] = Field(None, min_length=1, max_length=50, description="联系人姓名")
    contact_phone: Optional[str] = Field(None, min_length=1, max_length=20, description="联系电话")
    is_active: Optional[bool] = Field(None, description="是否有效")
