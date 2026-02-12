"""
认证服务 - 微信 code2session、获取或创建用户
支持 Refresh Token 机制
"""
import random
import string
import hmac
from typing import Optional, Tuple

from sqlalchemy import select, exc as sqlalchemy_exc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.wechat import code2session
from app.core.security import create_access_token, create_refresh_token
from app.core.cache import get_redis_client
from app.core.exceptions import BusinessException


def _gen_anonymous_name() -> str:
    """生成匿名昵称，如「打工人xxxx」"""
    suffix = "".join(random.choices(string.digits, k=4))
    return f"打工人{suffix}"


async def get_or_create_user(db: AsyncSession, openid: str, unionid: Optional[str] = None) -> User:
    """根据 openid 查询或创建用户（带并发控制）"""
    # 先尝试查询用户
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()
    if user:
        return user

    # 用户不存在，创建新用户
    new_user = User(
        openid=openid,
        unionid=unionid,
        anonymous_name=_gen_anonymous_name(),
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except sqlalchemy_exc.IntegrityError as e:
        # 处理并发创建导致的唯一约束冲突
        await db.rollback()
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"Concurrent user creation detected for openid {openid}, retrying...")

        # 重试查询（可能其他请求已创建）
        result = await db.execute(select(User).where(User.openid == openid))
        user = result.scalar_one_or_none()
        if user:
            return user

        # 仍然不存在，可能是其他类型的错误
        raise BusinessException("用户创建失败：并发冲突")
    except Exception as e:
        await db.rollback()
        raise BusinessException(f"用户创建失败: {str(e)}")


async def login_with_code(db: AsyncSession, code: str) -> Optional[Tuple[str, str, User]]:
    """
    微信 code 登录：code2session -> 获取或创建用户 -> 生成 JWT 对。
    失败返回 None（OK: 登录失败返回 None 是正常流程）。

    Returns:
        (access_token, refresh_token, user) 或 None
    """
    data = await code2session(code)
    openid = data.get("openid")
    if not openid:
        return None  # OK: 微信登录失败返回 None 是正常流程
    unionid = data.get("unionid")
    user = await get_or_create_user(db, openid=openid, unionid=unionid)

    # 生成 Access Token 和 Refresh Token
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    # 将 Refresh Token 存储到 Redis（7天过期）
    redis = await get_redis_client()
    if redis:
        try:
            await redis.setex(
                f"refresh_token:{user.id}",
                7 * 24 * 60 * 60,  # 7天
                refresh_token
            )
        except Exception as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to store refresh token for user {user.id}: {e}")
            # Token 存储失败不应该阻止登录，继续返回

    return access_token, refresh_token, user


async def refresh_access_token(refresh_token: str, user_id: str) -> Optional[Tuple[str, str]]:
    """
    使用 Refresh Token 刷新 Access Token

    Args:
        refresh_token: 旧的 refresh token
        user_id: 用户ID

    Returns:
        (new_access_token, new_refresh_token) 或 None
    """
    import hmac
    from app.core.security import decode_token, verify_token_type

    # 验证 Refresh Token
    payload = decode_token(refresh_token)
    if not payload or payload.get("sub") != user_id:
        return None

    if not verify_token_type(refresh_token, "refresh"):
        return None

    # 验证 Redis 中的 Refresh Token
    redis = await get_redis_client()
    if redis:
        try:
            # 首先检查 token 是否已被撤销（重放攻击检测）
            is_revoked = await redis.sismember(f"revoked_tokens:{user_id}", refresh_token)
            if is_revoked:
                from app.utils.logger import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Detected replay attack: revoked refresh token used for user {user_id}")
                return None

            stored_token = await redis.get(f"refresh_token:{user_id}")
            # 使用常量时间比较防止时序攻击
            if not stored_token or not hmac.compare_digest(stored_token, refresh_token):
                return None
        except Exception as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to verify refresh token for user {user_id}: {e}")
            return None

    # 生成新的 Token 对
    new_access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})

    # 使用 Redis 管道确保原子性操作
    if redis:
        try:
            pipe = redis.pipeline()
            # 将旧 refresh token 添加到已撤销列表（用于检测重放）
            pipe.sadd(f"revoked_tokens:{user_id}", refresh_token)
            # 设置已撤销列表的过期时间为7天
            pipe.expire(f"revoked_tokens:{user_id}", 7 * 24 * 60 * 60)
            # 更新当前有效的 refresh token
            pipe.setex(
                f"refresh_token:{user_id}",
                7 * 24 * 60 * 60,  # 7天
                new_refresh_token
            )
            # 执行管道中的所有命令
            await pipe.execute()
        except Exception as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to update refresh token for user {user_id}: {e}")
            # Token 更新失败是严重错误，返回 None 让客户端重试
            return None

    return new_access_token, new_refresh_token


async def revoke_refresh_token(user_id: str) -> None:
    """
    撤销用户的 Refresh Token（登出时调用）

    Args:
        user_id: 用户ID
    """
    redis = await get_redis_client()
    if redis:
        try:
            pipe = redis.pipeline()
            # 删除当前有效的 refresh token
            pipe.delete(f"refresh_token:{user_id}")
            # 清除已撤销的 tokens 列表
            pipe.delete(f"revoked_tokens:{user_id}")
            # 执行管道命令
            await pipe.execute()
        except Exception as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Failed to revoke refresh token for user {user_id}: {e}")
            # 登出时失败不严重，继续流程
