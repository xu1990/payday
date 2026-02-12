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
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    # Redis（技术方案 2.3）
    redis_url: str = "redis://127.0.0.1:6379/0"

    # 微信小程序（技术方案 2.1）
    wechat_app_id: str = ""
    wechat_app_secret: str = ""

    # JWT（技术方案 2.1 认证）
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 天

    # 金额加密（技术方案 2.2.3）
    encryption_secret_key: str = "change-me-32-bytes-key-for-fernet!!"

    # 腾讯云 COS（技术方案 1.2.2）
    cos_secret_id: str = ""
    cos_secret_key: str = ""
    cos_region: str = "ap-guangzhou"
    cos_bucket: str = "payday"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
