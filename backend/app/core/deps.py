"""
依赖注入 - 技术方案 2.1.1 core/deps.py
"""
from typing import Optional

from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .security import decode_token
from .signature import verify_signature, verify_timestamp
from .rate_limit import (
    RateLimiter,
    get_client_identifier,
    RATE_LIMIT_GENERAL,
    RATE_LIMIT_LOGIN,
    RATE_LIMIT_POST,
    RATE_LIMIT_COMMENT,
)
from app.models.user import User
from app.models.admin import AdminUser

security = HTTPBearer(auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的 token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.status != "normal":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_admin(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AdminUser:
    """管理端：要求 Bearer token 且 payload.scope == 'admin'，按 sub 查 AdminUser"""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("scope") != "admin" or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或非管理员 token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    admin_id = payload["sub"]
    result = await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return admin


async def verify_request_signature(
    request: Request,
    x_timestamp: Optional[str] = Header(None),
    x_nonce: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None),
) -> bool:
    """
    验证请求签名（可选依赖，根据需要启用）

    SECURITY: 签名验证现在是可选的
    - 如果请求包含签名头部，则进行验证
    - 如果请求不包含签名头部，则跳过验证（改用 JWT 认证）
    - 这允许逐步迁移到仅使用 JWT 的方式

    使用方式:
        @router.post("/api/endpoint")
        async def endpoint(
            ...,
            _sig: bool = Depends(verify_request_signature)
        ):
            ...
    """
    # 如果没有提供签名头部，跳过验证（使用 JWT 认证）
    if not all([x_timestamp, x_nonce, x_signature]):
        # 签名是可选的，依靠 JWT 认证即可
        return True

    # 开发环境可以跳过签名验证（但需要记录警告）
    from .config import get_settings
    import logging
    settings = get_settings()

    if settings.debug:
        # 在生产环境中永远不应该跳过安全验证
        # 如果需要在生产环境调试，应该使用单独的调试端点
        logger = logging.getLogger(__name__)
        logger.warning(
            "⚠️ Signature verification SKIPPED in DEBUG mode. "
            "This should NEVER happen in production."
        )
        return True

    # 验证时间戳
    verify_timestamp(x_timestamp, max_age_seconds=300)

    # 获取请求体
    try:
        # 对于 JSON 请求，需要获取 body 进行签名验证
        body = await request.json() if request.method in ["POST", "PUT", "PATCH"] else None
    except Exception:
        body = None

    # 验证签名
    url_path = request.url.path
    verify_signature(
        url=url_path,
        method=request.method,
        timestamp=x_timestamp,
        nonce=x_nonce,
        received_signature=x_signature,
        body=body,
    )

    return True


async def rate_limit_general(request: Request) -> bool:
    """
    一般 API 速率限制：100次/分钟

    使用方式:
        @router.post("/api/endpoint")
        async def endpoint(
            ...,
            _rate_limit: bool = Depends(rate_limit_general)
        ):
            ...
    """
    identifier = await get_client_identifier(request)
    await RATE_LIMIT_GENERAL.check(identifier, request)
    return True


async def rate_limit_login(request: Request) -> bool:
    """
    登录 API 速率限制：5次/分钟

    防止暴力破解
    """
    identifier = await get_client_identifier(request)
    await RATE_LIMIT_LOGIN.check(identifier, request)
    return True


async def rate_limit_post(request: Request) -> bool:
    """
    发帖 API 速率限制：10次/分钟

    防止垃圾内容发布
    """
    identifier = await get_client_identifier(request)
    await RATE_LIMIT_POST.check(identifier, request)
    return True


async def rate_limit_comment(request: Request) -> bool:
    """
    评论 API 速率限制：20次/分钟

    防止垃圾评论
    """
    identifier = await get_client_identifier(request)
    await RATE_LIMIT_COMMENT.check(identifier, request)
    return True


__all__ = [
    "get_db",
    "get_current_user",
    "get_current_admin",
    "verify_request_signature",
    "rate_limit_general",
    "rate_limit_login",
    "rate_limit_post",
    "rate_limit_comment",
]
