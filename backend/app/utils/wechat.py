"""
微信小程序 code2session - 技术方案 2.1 认证
"""
from typing import Optional

import httpx
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
    from app.core.cache import get_redis_client
    from app.utils.logger import get_logger
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


async def get_unlimited_qrcode(
    scene: str,
    page: str = "pages/index",
    width: int = 430,
    auto_color: bool = False,
    line_color: dict = None,
    is_hyaline: bool = False,
    check_path: bool = True
) -> bytes:
    """
    获取微信小程序码（无限制）
    https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/qrcode-link/qr-code/getUnlimitedQRCode.html

    Args:
        scene: 场景值（最多32个字符），如 "recordId=xxx" 或 "postId=xxx"
        page: 小程序页面路径，如 "pages/index"
        width: 二维码宽度，默认 430
        auto_color: 自动配置线条颜色
        line_color: 线条颜色，{"r": 0, "g": 0, "b": 0}
        is_hyaline: 是否需要透明底色
        check_path: 检查页面是否存在

    Returns:
        PNG 图片的二进制数据
    """
    import hashlib

    from app.core.cache import get_redis_client
    from app.utils.logger import get_logger
    logger = get_logger(__name__)

    settings = get_settings()

    # 生成缓存键
    cache_key = f"wxa:qrcode:{hashlib.md5(f'{scene}:{page}'.encode()).hexdigest()}"

    # 尝试从 Redis 获取缓存的小程序码
    redis = await get_redis_client()
    if redis:
        try:
            cached_qr = await redis.get(cache_key)
            if cached_qr:
                logger.info(f"Using cached mini-program code for {scene}")
                return cached_qr
        except Exception as e:
            logger.warning(f"Failed to get cached QR code: {e}")

    # 获取 access_token
    access_token = await get_access_token()

    # 调用微信 API
    url = "https://api.weixin.qq.com/wxa/getwxacodeunlimit"
    params = {"access_token": access_token}

    data = {
        "scene": scene,
        "page": page,
        "width": width,
        "auto_color": auto_color,
        "is_hyaline": is_hyaline,
        "check_path": check_path
    }

    if auto_color and line_color:
        data["line_color"] = line_color

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, params=params, json=data)

            # 检查响应是否为错误（JSON 格式）
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                result = resp.json()
                logger.error(f"Failed to generate mini-program code: {result}")
                raise Exception(f"Failed to generate QR code: {result}")
            else:
                # 返回的是图片二进制数据
                qr_data = resp.content

                # 缓存到 Redis（7天）
                if redis:
                    try:
                        await redis.setex(cache_key, 7 * 24 * 3600, qr_data)
                        logger.info(f"Cached mini-program code for {scene}")
                    except Exception as e:
                        logger.warning(f"Failed to cache QR code: {e}")

                logger.info(f"Successfully generated mini-program code for {scene}")
                return qr_data

    except Exception as e:
        logger.error(f"Error generating mini-program code: {e}")
        raise
