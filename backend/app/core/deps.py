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
from .csrf import csrf_manager, CSRFException
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
    # 检查admin账户是否启用
    if admin.is_active != "1":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员账户已被禁用",
        )
    return admin


def require_permission(required_role: str = "admin"):
    """
    权限检查依赖工厂函数

    Args:
        required_role: 需要的最低角色等级: superadmin > admin > readonly

    使用方式:
        @router.put("/posts/{post_id}/status")
        async def admin_post_update_status(
            ...,
            _perm: bool = Depends(require_permission("admin")),
            ...
        ):
    """
    async def check_permission(admin: AdminUser = Depends(get_current_admin)) -> bool:
        # 角色等级
        role_hierarchy = {
            "superadmin": 3,
            "admin": 2,
            "readonly": 1
        }

        admin_role = getattr(admin, "role", "admin")
        admin_level = role_hierarchy.get(admin_role, 2)  # 默认admin
        required_level = role_hierarchy.get(required_role, 2)

        if admin_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要 {required_role} 或更高级别角色",
            )
        return True

    return check_permission


async def verify_csrf_token(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
) -> bool:
    """
    验证 CSRF token（用于状态变更操作）

    使用方式:
        @router.delete("/admin/endpoint")
        async def endpoint(..., _csrf: bool = Depends(verify_csrf_token)):
            ...

    安全说明:
        - GET 和登录操作不需要 CSRF 验证
        - POST/PUT/DELETE 等状态变更操作需要验证
        - 使用 Redis 存储 token，避免内存多实例问题
        - 使用常量时间比较防止时序攻击
    """
    # 安全的GET请求方法（标准REST只读操作）
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    # 对于安全方法，检查是否有query parameters
    # 如果有query parameters，仍然需要CSRF验证（防止通过GET参数执行状态变更）
    if request.method in SAFE_METHODS:
        # 定义允许跳过CSRF的只读参数（如分页、排序、过滤等）
        READONLY_PARAMS = {
            "page", "page_size", "limit", "offset",
            "sort", "order", "search", "query",
            "user_id", "industry", "city", "salary_range",
            "status", "start_date", "end_date",
            "tag", "tags", "category", "type"
        }

        # 如果有query参数，检查是否都是已知的只读参数
        if request.query_params:
            param_names = set(request.query_params.keys())
            # 如果存在非只读参数，需要CSRF验证
            if not param_names.issubset(READONLY_PARAMS):
                # 有可疑的参数，需要CSRF验证
                is_valid = await csrf_manager.validate_token(request, str(admin.id))
                if not is_valid:
                    raise CSRFException("CSRF token 无效或已过期，请重新登录")

        # 标准的只读GET请求，跳过CSRF验证
        return True

    # POST/PUT/DELETE/PATCH 等状态变更操作必须验证 CSRF token
    is_valid = await csrf_manager.validate_token(request, str(admin.id))
    if not is_valid:
        raise CSRFException("CSRF token 无效或已过期，请重新登录")

    return True


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

    # 开发环境记录但不跳过验证
    from .config import get_settings
    import logging
    settings = get_settings()

    if settings.debug:
        # 开发模式仍然验证签名，只记录调试信息
        logger = logging.getLogger(__name__)
        logger.debug(
            "🔍 Signature verification enabled (DEBUG mode)"
        )
        # 不返回 True，继续执行签名验证

    # 始终验证时间戳 - 不允许绕过
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
    "verify_csrf_token",
    "verify_request_signature",
    "rate_limit_general",
    "rate_limit_login",
    "rate_limit_post",
    "rate_limit_comment",
]
