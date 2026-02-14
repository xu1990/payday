"""
管理端认证 - 按用户名查管理员、校验密码、签发 JWT（scope=admin）
支持 CSRF token 生成
支持 Refresh Token 机制
"""
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_token, verify_token_type
from app.core.security import verify_password
from app.models.admin import AdminUser
from app.core.csrf import csrf_manager
from app.core.cache import get_redis_client


async def get_admin_by_username(db: AsyncSession, username: str) -> Optional[AdminUser]:
    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    return result.scalar_one_or_none()


async def login_admin(db: AsyncSession, username: str, password: str) -> Optional[Tuple[str, str]]:
    """
    校验用户名密码，成功返回 (JWT, CSRF token)，失败返回 None

    Returns:
        (jwt_token, csrf_token) 或 None
    """
    admin = await get_admin_by_username(db, username)
    if not admin or not password or not verify_password(password, admin.password_hash):
        return None  # OK: 登录失败返回 None 是正常流程

    # 生成 JWT token
    jwt_token = create_access_token(data={"sub": str(admin.id), "scope": "admin"})

    # 生成并保存 CSRF token
    csrf_token = await csrf_manager.generate_token()
    await csrf_manager.save_token(csrf_token, str(admin.id))

    return jwt_token, csrf_token


async def refresh_admin_token(
    db: AsyncSession, refresh_token: str
) -> Optional[Tuple[str, str, str]]:
    """
    使用 Refresh Token 刷新管理员 Access Token

    Args:
        db: 数据库会话
        refresh_token: 旧的 refresh token

    Returns:
        (new_access_token, new_csrf_token, new_refresh_token) 或 None

    SECURITY:
    - 验证 Refresh Token 的有效性
    - 防止重放攻击
    - 使用 Redis 管理 token 状态
    - 撤销旧的 refresh token
    """
    from app.utils.logger import get_logger
    logger = get_logger(__name__)

    # 验证 Refresh Token
    payload = decode_token(refresh_token)
    if not payload or payload.get("sub") is None:
        logger.warning("Invalid refresh token: missing subject")
        return None

    if not verify_token_type(refresh_token, "refresh"):
        logger.warning("Invalid refresh token: wrong token type")
        return None

    admin_id = payload.get("sub")

    # 验证 Redis 中的 Refresh Token
    redis = await get_redis_client()
    if redis:
        try:
            # SECURITY: 检查 token 是否已被撤销（重放攻击检测）
            is_revoked = await redis.sismember(f"revoked_admin_tokens:{admin_id}", refresh_token)
            if is_revoked:
                logger.warning(f"Detected replay attack: revoked refresh token used for admin {admin_id}")
                return None

            stored_token = await redis.get(f"admin_refresh_token:{admin_id}")
            # 使用常量时间比较防止时序攻击
            import hmac
            if not stored_token or not hmac.compare_digest(stored_token, refresh_token):
                logger.warning(f"Invalid refresh token for admin {admin_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to verify refresh token for admin {admin_id}: {e}")
            return None

    # 验证管理员是否存在且未禁用
    admin = await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    admin = admin.scalar_one_or_none()
    if not admin or admin.status != "normal":
        logger.warning(f"Admin not found or disabled: {admin_id}")
        return None

    # 生成新的 Token 对
    new_access_token = create_access_token(data={"sub": admin_id, "scope": "admin"})
    new_csrf_token = await csrf_manager.generate_token()
    new_refresh_token = create_access_token(
        data={"sub": admin_id, "scope": "admin"}, token_type="refresh"
    )

    # 使用 Redis 管道确保原子性操作
    if redis:
        try:
            pipe = redis.pipeline()
            # 将旧 refresh token 添加到已撤销列表（用于检测重放）
            pipe.sadd(f"revoked_admin_tokens:{admin_id}", refresh_token)
            # 设置已撤销列表的过期时间为7天
            pipe.expire(f"revoked_admin_tokens:{admin_id}", 7 * 24 * 60 * 60)
            # 更新当前有效的 refresh token
            pipe.setex(
                f"admin_refresh_token:{admin_id}",
                7 * 24 * 60 * 60,  # 7天
                new_refresh_token
            )
            # 保存新的 CSRF token
            pipe.setex(
                f"csrf_token:{admin_id}",
                24 * 60 * 60,  # 24小时
                new_csrf_token
            )
            # 执行管道中的所有命令
            await pipe.execute()
        except Exception as e:
            logger.error(f"Failed to update refresh token for admin {admin_id}: {e}")
            # Token 更新失败是严重错误，返回 None 让客户端重试
            return None

    logger.info(f"Admin {admin_id} token refreshed successfully")
    return new_access_token, new_csrf_token, new_refresh_token
