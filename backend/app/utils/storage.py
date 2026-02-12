"""
统一存储服务 - 抽象层，支持腾讯云 COS 和阿里云 OSS
根据配置自动选择存储服务提供商
"""
from typing import Optional

from app.core.config import settings
from app.utils.cos import cos_service as _cos_service
from app.utils.oss import oss_service as _oss_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UnifiedStorageService:
    """
    统一存储服务抽象层

    根据配置的 storage_provider 自动选择：
    - "cos": 腾讯云 COS
    - "oss": 阿里云 OSS
    """

    def __init__(self):
        """初始化存储服务"""
        self._provider = settings.storage_provider.lower()
        self._validate_provider()

    def _validate_provider(self):
        """验证存储服务提供商配置"""
        valid_providers = ["cos", "oss"]
        if self._provider not in valid_providers:
            logger.warning(
                f"未知的存储服务提供商: {self._provider}，"
                f"有效值: {valid_providers}，将使用默认: cos"
            )
            self._provider = "cos"

    @property
    def cos_enabled(self) -> bool:
        """COS 是否启用"""
        return self._provider == "cos" and _cos_service.enabled

    @property
    def oss_enabled(self) -> bool:
        """OSS 是否启用"""
        return self._provider == "oss" and _oss_service.enabled

    @property
    def enabled(self) -> bool:
        """存储服务是否启用"""
        return self.cos_enabled or self.oss_enabled

    @property
    def current_provider(self) -> str:
        """当前使用的存储服务提供商"""
        return self._provider

    def generate_key(self, prefix: str = "images", ext: str = "jpg") -> str:
        """
        生成对象键（文件路径）

        Args:
            prefix: 路径前缀
            ext: 文件扩展名

        Returns:
            对象键，如: images/2024/01/15/uuid.jpg
        """
        if self._provider == "oss" and _oss_service.enabled:
            return _oss_service.generate_key(prefix, ext)
        else:
            return _cos_service.generate_key(prefix, ext)

    async def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """
        上传二进制数据

        Args:
            data: 文件二进制数据
            key: 对象键
            content_type: MIME 类型

        Returns:
            文件访问 URL

        Raises:
            Exception: 上传失败或服务未启用
        """
        if not self.enabled:
            raise Exception(
                f"存储服务未启用，当前配置: {self._provider}，"
                f"请检查对应服务的配置信息"
            )

        if self._provider == "oss" and _oss_service.enabled:
            logger.info(f"使用阿里云 OSS 上传: {key}")
            return await _oss_service.upload_bytes(data, key, content_type)
        else:
            logger.info(f"使用腾讯云 COS 上传: {key}")
            return await _cos_service.upload_bytes(data, key, content_type)

    async def upload_file(
        self,
        file_path: str,
        key: str,
    ) -> str:
        """
        上传本地文件

        Args:
            file_path: 本地文件路径
            key: 对象键

        Returns:
            文件访问 URL
        """
        if not self.enabled:
            raise Exception(
                f"存储服务未启用，当前配置: {self._provider}，"
                f"请检查对应服务的配置信息"
            )

        if self._provider == "oss" and _oss_service.enabled:
            logger.info(f"使用阿里云 OSS 上传文件: {key}")
            return await _oss_service.upload_file(file_path, key)
        else:
            logger.info(f"使用腾讯云 COS 上传文件: {key}")
            return await _cos_service.upload_file(file_path, key)

    def get_presigned_url(self, key: str, expires: int = 3600) -> str:
        """
        生成预签名 URL（用于私有文件访问）

        Args:
            key: 对象键
            expires: 过期时间（秒）

        Returns:
            预签名 URL
        """
        if not self.enabled:
            raise Exception(
                f"存储服务未启用，当前配置: {self._provider}，"
                f"请检查对应服务的配置信息"
            )

        if self._provider == "oss" and _oss_service.enabled:
            return _oss_service.get_presigned_url(key, expires)
        else:
            return _cos_service.get_presigned_url(key, expires)

    async def delete_object(self, key: str) -> bool:
        """
        删除对象

        Args:
            key: 对象键

        Returns:
            是否成功
        """
        if not self.enabled:
            logger.warning(f"存储服务未启用，无法删除对象: {key}")
            return False

        if self._provider == "oss" and _oss_service.enabled:
            return await _oss_service.delete_object(key)
        else:
            return await _cos_service.delete_object(key)

    def get_status(self) -> dict:
        """
        获取存储服务状态

        Returns:
            状态信息字典
        """
        return {
            "provider": self._provider,
            "cos_enabled": _cos_service.enabled,
            "oss_enabled": _oss_service.enabled,
            "current_service": "阿里云 OSS" if self._provider == "oss" else "腾讯云 COS",
            "healthy": self.enabled,
        }


# 单例实例
storage_service = UnifiedStorageService()


# 向后兼容的导出
# 保持原有的 cos_service 导出可用，但推荐使用 storage_service
__all__ = ["storage_service", "UnifiedStorageService"]
