"""
薪日 PayDay 主服务配置 - 与技术方案 v1.0 一致
从环境变量读取 MySQL/Redis/COS/微信等配置
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets
import logging
import string

logger = logging.getLogger(__name__)


def check_key_strength(key: str, min_length: int = 32) -> tuple[bool, str]:
    """
    检查密钥强度（熵值和随机性）

    Returns:
        (is_strong, error_message): 密钥是否足够强，以及错误信息
    """
    # 长度检查
    if len(key) < min_length:
        return False, f"长度不足: {len(key)} 字节，至少需要 {min_length} 字节"

    # 唯一字符比例检查（熵值检查）
    unique_chars = set(key)
    unique_ratio = len(unique_chars) / len(key)
    if unique_ratio < 0.5:
        return False, f"密钥熵值过低: 唯一字符仅占 {unique_ratio:.1%}，建议使用随机密钥"

    # 字符类别多样性检查
    has_upper = any(c in string.ascii_uppercase for c in key)
    has_lower = any(c in string.ascii_lowercase for c in key)
    has_digit = any(c in string.digits for c in key)
    has_special = any(c in string.punctuation for c in key)

    category_count = sum([has_upper, has_lower, has_digit, has_special])
    if category_count < 2:
        return False, f"密钥字符类别单一，建议包含大小写字母、数字和特殊字符中的至少2类"

    # 弱模式检查
    weak_patterns = [
        "change-me", "secret", "password", "key123", "test",
        "dev", "demo", "admin", "qwerty", "123456"
    ]
    key_lower = key.lower()
    for pattern in weak_patterns:
        if pattern in key_lower:
            return False, f"密钥包含弱模式 '{pattern}'"

    # 重复字符检查
    if len(key) > 8:
        # 检查是否有超过4个连续的相同字符
        for i in range(len(key) - 4):
            if key[i] == key[i+1] == key[i+2] == key[i+3] == key[i+4]:
                return False, "密钥包含过长重复字符序列"

    return (True, "")


class Settings(BaseSettings):
    """应用配置"""

    # 应用
    app_name: str = "薪日 PayDay"
    debug: bool = False

    # MySQL（技术方案 2.2）
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "payday"
    mysql_password: str = ""
    mysql_database: str = "payday_main"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    # Redis（技术方案 2.3）
    redis_url: str = "redis://127.0.0.1:6379/0"

    # 微信小程序（技术方案 2.1）
    wechat_app_id: str = ""
    wechat_app_secret: str = ""

    # 微信支付（技术方案 支付集成）
    wechat_mch_id: str = ""
    wechat_pay_api_key: str = ""
    wechat_pay_notify_url: str = ""

    # JWT（技术方案 2.1 认证）
    # SECURITY: 必须从环境变量设置，生产环境至少32字节
    jwt_secret_key: str  # 移除默认值，强制从环境变量读取
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 天

    # 金额加密（技术方案 2.2.3）
    # SECURITY: 必须从环境变量设置，必须是32字节URL安全的base64编码密钥
    encryption_secret_key: str  # 移除默认值，强制从环境变量读取

    # API 请求签名密钥（用于验证小程序请求）
    # SECURITY: 生产环境必须设置，与小程序端保持一致
    # 现在签名是可选的，主要用于向后兼容
    api_secret: str = ""  # 移除默认值，设为空字符串

    # CORS白名单（技术方案 安全）
    # SECURITY: 生产环境必须设置具体的允许源，多个用逗号分隔
    cors_origins: str = "http://localhost:5174,http://127.0.0.1:5174"

    # 腾讯云 COS（技术方案 1.2.2）
    cos_secret_id: str = ""
    cos_secret_key: str = ""
    cos_region: str = "ap-guangzhou"
    cos_bucket: str = "payday"

    # 阿里云 OSS 对象存储
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_endpoint: str = ""  # 如: oss-cn-hangzhou.aliyuncs.com
    oss_bucket: str = "payday"

    # 存储服务选择: cos | oss
    storage_provider: str = "cos"

    # 腾讯云天御内容安全
    tencent_secret_id: str = ""
    tencent_secret_key: str = ""
    tencent_region: str = "ap-guangzhou"
    tencent_yu_biz_type: str = "payday_risk_check"

    # 阿里云内容安全
    aliyun_secret_id: str = ""
    aliyun_secret_key: str = ""
    aliyun_region: str = "cn-hangzhou"
    aliyun_yu_biz_type: str = "payday_risk_check"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def validate_security_settings(self) -> None:
        """
        验证安全相关的配置项

        在生产环境中，某些配置必须正确设置
        """
        errors = []

        # JWT 密钥强度验证（包括熵值检查）
        jwt_strong, jwt_error = check_key_strength(self.jwt_secret_key, min_length=32)
        if not jwt_strong:
            errors.append(f"JWT_SECRET_KEY {jwt_error}")

        # 加密密钥强度验证（包括熵值检查）
        enc_strong, enc_error = check_key_strength(self.encryption_secret_key, min_length=32)
        if not enc_strong:
            errors.append(f"ENCRYPTION_SECRET_KEY {enc_error}")

        # CORS 配置检查（仅警告）
        if self.cors_origins == "*" or "localhost" in self.cors_origins:
            logger.warning(
                "⚠️ 生产环境中 CORS 配置包含 localhost 或通配符，建议设置具体的允许源"
            )

        if errors:
            error_msg = "安全配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors)
            if self.debug:
                logger.warning(f"⚠️ {error_msg}\n在调试模式下将继续运行，但生产环境必须修复这些问题")
            else:
                raise ValueError(error_msg)


# Module-level settings instance (for direct imports)
# Initialized on first import via get_settings()
_settings = None


@lru_cache
def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        # 在获取配置时进行验证
        _settings.validate_security_settings()
    return _settings


# For direct import: settings = get_settings()
# Use get_settings() for type hints and lazy loading
settings = get_settings()


def generate_secure_key(length: int = 43) -> str:
    """
    生成安全的随机密钥

    Args:
        length: 密钥长度，默认 43 字符（约 32 字节 base64 编码）

    Returns:
        URL 安全的 base64 编码随机密钥
    """
    return secrets.token_urlsafe(length)
