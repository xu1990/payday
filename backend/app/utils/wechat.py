"""
微信小程序 code2session - 技术方案 2.1 认证
"""
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
