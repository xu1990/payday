"""
认证服务 - 微信 code2session、获取或创建用户
"""
import random
import string
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.wechat import code2session
from app.core.security import create_access_token


def _gen_anonymous_name() -> str:
    """生成匿名昵称，如「打工人xxxx」"""
    suffix = "".join(random.choices(string.digits, k=4))
    return f"打工人{suffix}"


async def get_or_create_user(db: AsyncSession, openid: str, unionid: Optional[str] = None) -> User:
    """根据 openid 查询或创建用户"""
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(
        openid=openid,
        unionid=unionid,
        anonymous_name=_gen_anonymous_name(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_with_code(db: AsyncSession, code: str) -> Optional[Tuple[str, User]]:
    """
    微信 code 登录：code2session -> 获取或创建用户 -> 生成 JWT。
    失败返回 None。
    """
    data = await code2session(code)
    openid = data.get("openid")
    if not openid:
        return None
    unionid = data.get("unionid")
    user = await get_or_create_user(db, openid=openid, unionid=unionid)
    token = create_access_token(data={"sub": user.id})
    return token, user
