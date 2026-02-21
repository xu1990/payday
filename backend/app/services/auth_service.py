"""
认证服务 - 微信 code2session、获取或创建用户
支持 Refresh Token 机制
支持手机号登录
"""
import random
import string
import hmac
import re
from typing import Optional, Tuple

from sqlalchemy import select, exc as sqlalchemy_exc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.phone_lookup import PhoneLookup, hash_phone_number
from app.utils.wechat import code2session, get_phone_number_from_wechat
from app.core.security import create_access_token, create_refresh_token
from app.core.cache import get_redis_client
from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.utils.encryption import encrypt_amount, decrypt_amount


def _gen_anonymous_name() -> str:
    """生成匿名昵称，如「打工人xxxx」"""
    suffix = "".join(random.choices(string.digits, k=4))
    return f"打工人{suffix}"


async def get_or_create_user(db: AsyncSession, openid: str, unionid: Optional[str] = None) -> User:
    """根据 openid 查询或创建用户（带并发控制）

    SECURITY: 使用数据库无关的方式处理并发创建冲突
    1. 尝试创建新用户
    2. 如果 openid 已存在（IntegrityError），则查询现有用户
    3. 这种方式对 MySQL 和 SQLite 都有效
    """
    from app.utils.logger import get_logger
    logger = get_logger(__name__)

    # 首先尝试查询用户是否存在（避免不必要的插入尝试）
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()

    if user:
        logger.info(f"Existing user {user.id} found for openid {openid}")
        # 如果提供了新的 unionid，更新它
        if unionid and user.unionid != unionid:
            user.unionid = unionid
            await db.commit()
            await db.refresh(user)
        return user

    # 用户不存在，尝试创建
    new_user = User(
        openid=openid,
        unionid=unionid,
        anonymous_name=_gen_anonymous_name(),
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info(f"New user {new_user.id} created for openid {openid}")
        return new_user
    except sqlalchemy_exc.IntegrityError:
        # 并发请求：另一个请求已经创建了该用户
        # Rollback 并重新查询
        await db.rollback()
        result = await db.execute(select(User).where(User.openid == openid))
        user = result.scalar_one()
        logger.info(f"User {user.id} retrieved after concurrent creation attempt for openid {openid}")
        return user


async def bind_phone_to_user(db: AsyncSession, user_id: str, phone_number: str) -> bool:
    """
    绑定手机号到现有用户

    Args:
        db: 数据库会话
        user_id: 用户ID
        phone_number: 手机号（明文）

    Returns:
        绑定成功返回 True

    Raises:
        NotFoundException: 用户不存在
        ValidationException: 手机号格式无效
        BusinessException: 手机号已验证且不允许更改
    """
    from app.utils.logger import get_logger
    logger = get_logger(__name__)

    # 验证手机号格式（中国大陆手机号）
    phone_pattern = re.compile(r'^1[3-9]\d{9}$')
    if not phone_pattern.match(phone_number):
        raise ValidationException("手机号格式无效", details={"phone_number": phone_number})

    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("用户不存在", details={"user_id": user_id})

    # 检查是否已验证手机号
    if user.phone_verified == 1:
        logger.warning(f"User {user_id} already has verified phone number")
        raise BusinessException("手机号已验证，不允许更改", code="PHONE_ALREADY_VERIFIED")

    # 加密手机号
    encrypted_phone, salt = encrypt_amount(phone_number)
    # 存储格式: encrypted_phone:salt
    phone_with_salt = f"{encrypted_phone}:{salt}"

    # 计算手机号哈希值
    phone_hash = hash_phone_number(phone_number)

    # 更新用户手机号
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            phone_number=phone_with_salt,
            phone_verified=1
        )
    )

    # 创建 phone_lookup 记录
    phone_lookup = PhoneLookup(
        phone_hash=phone_hash,
        user_id=user_id
    )
    db.add(phone_lookup)

    await db.commit()
    await db.refresh(user)

    logger.info(f"Phone number bound to user {user_id}: {phone_number[:3]}****{phone_number[-4:]}")
    return True


async def get_user_by_phone(db: AsyncSession, phone_number: str) -> Optional[User]:
    """
    根据手机号查询用户（使用 phone_lookup 表，O(1) 复杂度）
    如果 phone_lookup 中没有记录，则回退到旧方法（遍历解密）以保持向后兼容

    Args:
        db: 数据库会话
        phone_number: 手机号（明文）

    Returns:
        用户对象或 None
    """
    from app.utils.logger import get_logger
    logger = get_logger(__name__)

    # 计算手机号哈希值
    phone_hash = hash_phone_number(phone_number)

    # 首先尝试使用 phone_lookup 表查询（O(1) 查询）
    result = await db.execute(
        select(User)
        .join(PhoneLookup, PhoneLookup.user_id == User.id)
        .where(PhoneLookup.phone_hash == phone_hash)
    )

    user = result.scalar_one_or_none()

    if user:
        logger.info(f"Found user {user.id} by phone number (using phone_lookup)")
        return user

    # 回退到旧方法：遍历解密（用于没有 phone_lookup 记录的旧数据）
    logger.info(f"No user found in phone_lookup, falling back to legacy method")
    result = await db.execute(
        select(User)
        .where(User.phone_number.isnot(None))
        .where(User.phone_verified == 1)
    )
    users = result.scalars().all()

    # 遍历用户，解密手机号进行匹配
    for old_user in users:
        if old_user.phone_number:
            try:
                # 存储格式: encrypted_phone:salt
                parts = old_user.phone_number.split(':')
                if len(parts) == 2:
                    encrypted, salt_b64 = parts
                    decrypted_phone = decrypt_amount(encrypted, salt_b64)
                    # decrypt_amount returns float, convert to string for comparison
                    decrypted_phone_str = str(int(decrypted_phone)) if decrypted_phone == int(decrypted_phone) else str(decrypted_phone)
                    if decrypted_phone_str == phone_number:
                        # 找到了用户，创建 phone_lookup 记录以便下次快速查找
                        logger.info(f"Found user {old_user.id} by phone number (legacy method), creating lookup record")
                        new_lookup = PhoneLookup(
                            phone_hash=phone_hash,
                            user_id=str(old_user.id)
                        )
                        db.add(new_lookup)
                        try:
                            await db.commit()
                        except Exception:
                            # 如果创建 lookup 失败（例如并发），不影响返回结果
                            await db.rollback()
                        return old_user
            except Exception as e:
                logger.warning(f"Failed to decrypt phone for user {old_user.id}: {e}")
                continue

    logger.info(f"No user found with phone number {phone_number}")
    return None


async def login_with_code(db: AsyncSession, code: str, phone_code: Optional[str] = None) -> Optional[Tuple[str, str, User]]:
    """
    微信 code 登录：code2session -> 获取或创建用户 -> 生成 JWT 对。
    支持可选的手机号绑定（通过 phone_code）。
    失败返回 None（OK: 登录失败返回 None 是正常流程）。

    Args:
        db: 数据库会话
        code: 微信登录 code
        phone_code: 可选的手机号 code（用于获取和绑定手机号）

    Returns:
        (access_token, refresh_token, user) 或 None
    """
    from datetime import datetime, timedelta
    from sqlalchemy import update

    # 开发环境模拟登录（如果未配置微信凭证）
    from app.core.config import get_settings
    settings = get_settings()

    if not settings.wechat_app_id or not settings.wechat_app_secret:
        # 开发环境：使用模拟 openid（仅用于开发测试）
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"[DEV_MODE] Using mock login - WECHAT_APP_ID or WECHAT_APP_SECRET not configured")

        # 使用 code 的前 28 位作为模拟 openid（避免重复）
        mock_openid = f"dev_openid_{code[:28]}"

        user = await get_or_create_user(db, openid=mock_openid, unionid=None)

        # 处理手机号绑定（开发环境模拟）
        if phone_code:
            # 开发环境：直接使用 phone_code 作为模拟手机号（仅用于测试）
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            mock_phone = f"1{phone_code[:10]}"  # 模拟11位手机号

            # 检查是否已有该手机号的用户
            existing_user_by_phone = await get_user_by_phone(db, mock_phone)
            if existing_user_by_phone:
                # 使用已有手机号的用户
                user = existing_user_by_phone
                logger.info(f"User {user.id} found by phone number in dev mode")
            elif user.phone_verified == 0:
                # 绑定手机号到当前用户
                try:
                    await bind_phone_to_user(db, str(user.id), mock_phone)
                    logger.info(f"Phone bound to user {user.id} in dev mode")
                except Exception as e:
                    logger.warning(f"Failed to bind phone in dev mode: {e}")
                    # 绑定失败不影响登录流程

        # 检查用户是否已注销
        if user.deactivated_at:
            # 自动恢复账号
            recovery_deadline = user.deactivated_at + timedelta(days=30)

            if datetime.utcnow() > recovery_deadline:
                # 超过30天，无法恢复
                raise BusinessException("账号已注销且超过恢复期限", code="ACCOUNT_PERMANENTLY_DELETED")

            # 在恢复期限内，自动恢复账号
            await db.execute(
                update(User).where(User.id == user.id).values(deactivated_at=None)
            )
            await db.commit()
            await db.refresh(user)
            logger.info(f"User {user.id} account reactivated after deactivation")

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
                logger.warning(f"Failed to store refresh token in Redis: {e}")

        return access_token, refresh_token, user

    # 生产环境：调用微信 code2session
    data = await code2session(code)
    if not data:
        return None  # OK: 微信登录失败返回 None 是正常流程
    openid = data.get("openid")
    if not openid:
        return None  # OK: 微信登录失败返回 None 是正常流程
    unionid = data.get("unionid")
    user = await get_or_create_user(db, openid=openid, unionid=unionid)

    # 处理手机号绑定（生产环境）
    if phone_code:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)

        # 从微信获取手机号
        phone_number = await get_phone_number_from_wechat(phone_code)

        if phone_number:
            # 检查是否已有该手机号的用户
            existing_user_by_phone = await get_user_by_phone(db, phone_number)
            if existing_user_by_phone and existing_user_by_phone.id != user.id:
                # 使用已有手机号的用户（账号合并逻辑）
                # 如果刚创建了新用户且 openid 不同，删除新用户
                if user.openid != existing_user_by_phone.openid:
                    logger.info(f"Merging accounts: keeping existing user {existing_user_by_phone.id}, deleting newly created {user.id}")
                    # 删除刚创建的重复用户
                    await db.delete(user)
                    await db.commit()
                    user = existing_user_by_phone
                    await db.refresh(user)
                else:
                    # openid 相同，直接使用已有用户
                    user = existing_user_by_phone
                logger.info(f"User {user.id} found by phone number, using existing account")
            elif user.phone_verified == 0:
                # 绑定手机号到当前用户
                try:
                    await bind_phone_to_user(db, str(user.id), phone_number)
                    logger.info(f"Phone bound to user {user.id}")
                except Exception as e:
                    logger.warning(f"Failed to bind phone: {e}")
                    # 绑定失败不影响登录流程
        else:
            logger.warning(f"Failed to get phone number from WeChat with code {phone_code}")
            # 获取手机号失败不影响登录流程

    # 检查用户是否已注销
    if user.deactivated_at:
        # 自动恢复账号
        recovery_deadline = user.deactivated_at + timedelta(days=30)

        if datetime.utcnow() > recovery_deadline:
            # 超过30天，无法恢复
            raise BusinessException("账号已注销且超过恢复期限", code="ACCOUNT_PERMANENTLY_DELETED")

        # 在恢复期限内，自动恢复账号
        await db.execute(
            update(User).where(User.id == user.id).values(deactivated_at=None)
        )
        await db.commit()
        await db.refresh(user)
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info(f"User {user.id} account reactivated after deactivation")

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
