"""
CSRF 保护 - 双重提交 Cookie 模式
保护管理后台免受跨站请求伪造攻击
"""
import secrets
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.core.cache import get_redis_client


class CSRFTokenManager:
    """CSRF Token 管理器"""

    def __init__(self):
        self.token_length = 32
        self.cookie_name = "csrf_token"
        self.header_name = "X-CSRF-Token"
        self.cache_prefix = "csrf:"

    async def generate_token(self) -> str:
        """生成随机 CSRF token"""
        return secrets.token_urlsafe(self.token_length)

    async def save_token(self, token: str, user_id: str, ttl: int = 3600) -> None:
        """
        保存 CSRF token 到 Redis

        Args:
            token: CSRF token
            user_id: 用户ID
            ttl: 过期时间（秒），默认1小时
        """
        redis = await get_redis_client()
        if redis:
            key = f"{self.cache_prefix}{user_id}"
            await redis.setex(key, ttl, token)

    async def validate_token(
        self,
        request: Request,
        user_id: str
    ) -> bool:
        """
        验证 CSRF token

        Args:
            request: FastAPI 请求对象
            user_id: 用户ID

        Returns:
            True if token is valid, False otherwise
        """
        # 从 header 中获取 token
        token = request.headers.get(self.header_name)

        if not token:
            return False

        # 从 Redis 中获取存储的 token
        redis = await get_redis_client()
        if not redis:
            # Redis 不可用时拒绝请求（安全优先）
            return False

        key = f"{self.cache_prefix}{user_id}"
        stored_token = await redis.get(key)

        if not stored_token:
            return False

        # 使用常量时间比较防止时序攻击
        import hmac
        # 确保两个参数都是相同类型（都转换为bytes）
        token_bytes = token.encode('utf-8') if isinstance(token, str) else token
        stored_bytes = stored_token.encode('utf-8') if isinstance(stored_token, str) else stored_token
        return hmac.compare_digest(token_bytes, stored_bytes)

    async def delete_token(self, user_id: str) -> None:
        """删除用户的 CSRF token（登出时调用）"""
        redis = await get_redis_client()
        if redis:
            key = f"{self.cache_prefix}{user_id}"
            await redis.delete(key)


# 全局 CSRF 管理器实例
csrf_manager = CSRFTokenManager()


class CSRFException(HTTPException):
    """CSRF 验证失败异常"""

    def __init__(self, detail: str = "CSRF token validation failed"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def csrf_response(
    success: bool = True,
    message: str = "OK",
    csrf_token: Optional[str] = None,
    status_code: int = 200
) -> JSONResponse:
    """
    包含 CSRF token 的响应

    Args:
        success: 请求是否成功
        message: 响应消息
        csrf_token: CSRF token（如果有）
        status_code: HTTP 状态码

    Returns:
        JSONResponse with CSRF token in headers
    """
    content = {
        "success": success,
        "message": message,
    }

    headers = {}
    if csrf_token:
        headers[csrf_manager.header_name] = csrf_token

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers
    )
