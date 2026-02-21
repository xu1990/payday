"""认证相关 schema"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    code: str = Field(..., description="微信 wx.login 返回的 code")
    phoneNumberCode: Optional[str] = Field(None, description="微信手机号授权返回的 code")


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict  # 当前用户简要信息


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="刷新 Token")
    user_id: str = Field(..., description="用户ID")


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
