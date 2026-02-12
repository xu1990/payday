"""
认证接口 - POST /login 微信 code 登录
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import login_with_code

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await login_with_code(db, body.code)
    if not result:
        raise HTTPException(status_code=400, detail="微信登录失败，请重试")
    token, user = result
    user_info = {
        "id": user.id,
        "anonymous_name": user.anonymous_name,
        "avatar": user.avatar,
    }
    return LoginResponse(access_token=token, user=user_info)
