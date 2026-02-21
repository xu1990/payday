"""
微信小程序 code2session - 技术方案 2.1 认证
"""
import httpx
from typing import Optional
from app.core.config import get_settings


async def code2session(code: str) -> dict:
    """
    通过 code 换取 openid 和 session_key
    https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-login/code2Session.html
    """
    settings = get_settings()
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.wechat_app_id,
        "secret": settings.wechat_app_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()
    return data


async def get_phone_number_from_wechat(phone_code: str) -> Optional[str]:
    """
    使用 phone_code 获取用户手机号
    https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-info/phone-number/getPhoneNumber.html

    Args:
        phone_code: 微信小程序端获取手机号时返回的 code

    Returns:
        手机号字符串，失败返回 None
    """
    from app.utils.logger import get_logger
    logger = get_logger(__name__)

    settings = get_settings()
    url = "https://api.weixin.qq.com/wxa/business/getuserphonenumber"
    params = {
        "access_token": await get_access_token()
    }
    data = {
        "code": phone_code
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, params=params, json=data)
            result = resp.json()

            if result.get("errcode") == 0 and result.get("errmsg") == "ok":
                phone_info = result.get("phone_info", {})
                phone_number = phone_info.get("phoneNumber")
                logger.info(f"Successfully got phone number: {phone_number[:3]}****{phone_number[-4:]}")
                return phone_number
            else:
                logger.warning(f"Failed to get phone number: {result}")
                return None
    except Exception as e:
        logger.error(f"Error getting phone number from WeChat: {e}")
        return None


async def get_access_token() -> str:
    """
    获取小程序 access_token
    https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/access-token/getAccessToken.html

    Returns:
        access_token 字符串
    """
    from app.utils.logger import get_logger
    from app.core.cache import get_redis_client
    logger = get_logger(__name__)

    settings = get_settings()

    # 尝试从 Redis 获取缓存的 token
    redis = await get_redis_client()
    if redis:
        try:
            cached_token = await redis.get("wechat:access_token")
            if cached_token:
                return cached_token
        except Exception as e:
            logger.warning(f"Failed to get cached access token: {e}")

    # 从微信 API 获取新的 access_token
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": settings.wechat_app_id,
        "secret": settings.wechat_app_secret,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        result = resp.json()

        if "access_token" in result:
            access_token = result["access_token"]
            expires_in = result.get("expires_in", 7200)

            # 缓存到 Redis，提前5分钟过期
            if redis:
                try:
                    await redis.setex(
                        "wechat:access_token",
                        expires_in - 300,
                        access_token
                    )
                except Exception as e:
                    logger.warning(f"Failed to cache access token: {e}")

            return access_token
        else:
            logger.error(f"Failed to get access token: {result}")
            raise Exception(f"Failed to get WeChat access token: {result}")
