"""
管理端认证 - 按用户名查管理员、校验密码、签发 JWT（scope=admin）
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.models.admin import AdminUser


async def get_admin_by_username(db: AsyncSession, username: str) -> Optional[AdminUser]:
    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    return result.scalar_one_or_none()


async def login_admin(db: AsyncSession, username: str, password: str) -> Optional[str]:
    """校验用户名密码，成功返回 JWT（payload 含 sub=admin_id, scope=admin），失败返回 None"""
    admin = await get_admin_by_username(db, username)
    if not admin or not verify_password(password, admin.password_hash):
        return None  # OK: 登录失败返回 None 是正常流程
    token = create_access_token(data={"sub": str(admin.id), "scope": "admin"})
    return token
