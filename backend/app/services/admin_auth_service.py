"""
管理端认证 - 按用户名查管理员、校验密码、签发 JWT（scope=admin）
支持 CSRF token 生成
"""
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.models.admin import AdminUser
from app.core.csrf import csrf_manager


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
    if not admin or not verify_password(password, admin.password_hash):
        return None  # OK: 登录失败返回 None 是正常流程

    # 生成 JWT token
    jwt_token = create_access_token(data={"sub": str(admin.id), "scope": "admin"})

    # 生成并保存 CSRF token
    csrf_token = await csrf_manager.generate_token()
    await csrf_manager.save_token(csrf_token, str(admin.id))

    return jwt_token, csrf_token
