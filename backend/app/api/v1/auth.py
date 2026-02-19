"""
认证接口 - POST /login 微信 code 登录
支持 Refresh Token 机制
"""
from fastapi import APIRouter, Depends
from app.core.exceptions import BusinessException, AuthenticationException, success_response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, rate_limit_login, rate_limit_general
from app.core.security import verify_token_type
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse
from app.services.auth_service import login_with_code, refresh_access_token, revoke_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", dependencies=[Depends(rate_limit_login)])
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await login_with_code(db, body.code)
    if not result:
        raise BusinessException("请求参数错误", code="VALIDATION_ERROR")
    access_token, refresh_token, user = result
    user_info = {
        "id": user.id,
        "anonymous_name": user.anonymous_name,
        "avatar": user.avatar,
    }
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user_info
    }
    return success_response(data=data, message="登录成功")


@router.post("/refresh")
async def refresh(
    body: RefreshTokenRequest,
):
    """
    刷新 Access Token

    需要提供有效的 Refresh Token 和用户ID
    """
    result = await refresh_access_token(body.refresh_token, body.user_id)
    if not result:
        raise AuthenticationException("认证失败", code="AUTH_FAILED")

    new_access_token, new_refresh_token = result
    data = {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }
    return success_response(data=data, message="刷新成功")


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """
    登出 - 撤销 Refresh Token
    """
    await revoke_refresh_token(current_user.id)
    return success_response(message="登出成功")
