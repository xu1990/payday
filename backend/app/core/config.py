"""
薪日 PayDay 主服务配置 - 与技术方案 v1.0 一致
从环境变量读取 MySQL/Redis/COS/微信等配置
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


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
    api_secret: str = "dev-api-secret-key-for-signing"  # 开发环境默认值

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
