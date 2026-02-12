"""认证相关 schema"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    code: str = Field(..., description="微信 wx.login 返回的 code")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict  # 当前用户简要信息
