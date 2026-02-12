"""
JWT 认证与密码哈希 - 技术方案 2.1 认证与 2.2.3；管理端 passlib
支持 Refresh Token 机制
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """密码哈希（管理端登录）"""
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """校验密码"""
    return pwd_ctx.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Access Token（短期，15分钟）"""
    settings = get_settings()
    to_encode = data.copy()
    # Access Token 有效期较短（15分钟）
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(data: dict) -> str:
    """创建 JWT Refresh Token（长期，7天）"""
    settings = get_settings()
    to_encode = data.copy()
    # Refresh Token 有效期较长（7天）
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> Optional[dict]:
    """解析 JWT Token，失败返回 None"""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token_type(token: str, expected_type: str) -> bool:
    """验证 Token 类型"""
    payload = decode_token(token)
    if not payload:
        return False
    return payload.get("type") == expected_type
