"""
腾讯云 COS 对象存储服务 - 图片上传
"""
import uuid
from datetime import timedelta
from typing import Optional

from qcloud_cos import CosConfig, CosS3Client
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CosService:
    """腾讯云 COS 对象存储服务"""

    def __init__(self):
        """初始化 COS 客户端"""
        self._client: Optional[CosS3Client] = None
        self._enabled = bool(settings.cos_secret_id and settings.cos_secret_key and settings.cos_bucket)

    @property
    def client(self) -> Optional[CosS3Client]:
        """获取 COS 客户端（懒加载）"""
        if not self._enabled:
            return None

        if self._client is None:
            config = CosConfig(
                Region=settings.cos_region,
                SecretId=settings.cos_secret_id,
                SecretKey=settings.cos_secret_key,
            )
            self._client = CosS3Client(config)

        return self._client

    @property
    def enabled(self) -> bool:
        """COS 是否启用"""
        return self._enabled

    def generate_key(self, prefix: str = "images", ext: str = "jpg") -> str:
        """
        生成对象键（文件路径）

        Args:
            prefix: 路径前缀
            ext: 文件扩展名

        Returns:
            对象键，如: images/2024/01/15/uuid.jpg
        """
        from datetime import datetime

        now = datetime.now()
        date_path = now.strftime("%Y/%m/%d")
        filename = f"{uuid.uuid4()}.{ext}"
        return f"{prefix}/{date_path}/{filename}"

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
            Exception: 上传失败
        """
        if not self.enabled:
            raise Exception("COS 服务未启用，请检查配置")

        try:
            response = self.client.put_object(
                Bucket=settings.cos_bucket,
                Body=data,
                Key=key,
                ContentType=content_type,
            )

            # 构建访问 URL
            # 如果桶是私有访问，需要生成预签名 URL
            # 如果桶是公共读，直接返回 URL
            url = f"https://{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com/{key}"

            logger.info(f"COS 上传成功: {key}")
            return url

        except Exception as e:
            logger.error(f"COS 上传失败: {e}")
            raise

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
            raise Exception("COS 服务未启用，请检查配置")

        try:
            response = self.client.upload_file(
                Bucket=settings.cos_bucket,
                LocalFilePath=file_path,
                Key=key,
            )
            url = f"https://{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com/{key}"
            logger.info(f"COS 文件上传成功: {key}")
            return url

        except Exception as e:
            logger.error(f"COS 文件上传失败: {e}")
            raise

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
            raise Exception("COS 服务未启用，请检查配置")

        try:
            url = self.client.get_presigned_url(
                Method='GET',
                Bucket=settings.cos_bucket,
                Key=key,
                Expired=expires,
            )
            return url

        except Exception as e:
            logger.error(f"生成预签名 URL 失败: {e}")
            raise

    async def delete_object(self, key: str) -> bool:
        """
        删除对象

        Args:
            key: 对象键

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        try:
            self.client.delete_object(
                Bucket=settings.cos_bucket,
                Key=key,
            )
            logger.info(f"COS 对象删除成功: {key}")
            return True

        except Exception as e:
            logger.error(f"COS 对象删除失败: {e}")
            return False


# 单例实例
cos_service = CosService()
