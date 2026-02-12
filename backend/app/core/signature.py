"""
请求签名验证 - HMAC-SHA256
用于验证来自小程序的请求签名
"""
import hashlib
import hmac
from typing import Dict, Any

from app.core.config import get_settings
from app.core.exceptions import ValidationException

settings = get_settings()


def verify_signature(
    url: str,
    method: str,
    timestamp: str,
    nonce: str,
    received_signature: str,
    body: Dict[str, Any] = None,
) -> bool:
    """
    验证请求签名

    Args:
        url: 请求 URL
        method: 请求方法
        timestamp: 时间戳
        nonce: 随机数
        received_signature: 接收到的签名
        body: 请求体（JSON）

    Returns:
        True if signature is valid

    Raises:
        ValidationException: 签名验证失败
    """
    # 获取 API 密钥（从环境变量）
    api_secret = getattr(settings, 'api_secret', None)
    if not api_secret:
        # 开发环境可以跳过签名验证
        if settings.debug:
            return True
        raise ValidationException("API signature secret not configured")

    # 构建待签名字符串（与前端保持一致）
    params = {"url": url, "method": method, "timestamp": timestamp, "nonce": nonce}
    if body:
        params.update(body)

    # 按字母顺序排序参数
    sorted_items = sorted(params.items())
    sign_str = "&".join([f"{k}={v}" for k, v in sorted_items])

    # 计算 HMAC-SHA256
    expected_signature = hmac.new(
        api_secret.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # 验证签名
    if not hmac.compare_digest(expected_signature, received_signature):
        raise ValidationException("Invalid request signature", details={
            "expected": expected_signature[:8] + "...",  # 只显示前8个字符
            "received": received_signature[:8] + "..."
        })

    return True


def verify_timestamp(timestamp_str: str, max_age_seconds: int = 60) -> bool:
    """
    验证时间戳是否在有效期内

    Args:
        timestamp_str: 时间戳字符串（秒）
        max_age_seconds: 最大有效期（秒），默认60秒（减少重放攻击窗口）

    Returns:
        True if timestamp is valid

    Raises:
        ValidationException: 时间戳过期
    """
    try:
        timestamp = int(timestamp_str)
    except (ValueError, TypeError):
        raise ValidationException("Invalid timestamp format")

    import time
    current_time = int(time.time())

    if abs(current_time - timestamp) > max_age_seconds:
        raise ValidationException(f"Request timestamp expired (max age: {max_age_seconds}s)")

    return True
