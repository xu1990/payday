"""
阿里云 OSS 对象存储服务 - 图片上传
"""
import uuid
from datetime import datetime
from typing import Optional

import oss2
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OssService:
    """阿里云 OSS 对象存储服务"""

    def __init__(self):
        """初始化 OSS 客户端"""
        self._auth: Optional[oss2.Auth] = None
        self._bucket: Optional[oss2.Bucket] = None
        self._enabled = bool(
            settings.oss_access_key_id
            and settings.oss_access_key_secret
            and settings.oss_bucket
            and settings.oss_endpoint
        )

    @property
    def auth(self) -> Optional[oss2.Auth]:
        """获取 OSS 认证对象（懒加载）"""
        if not self._enabled:
            return None

        if self._auth is None:
            self._auth = oss2.Auth(
                settings.oss_access_key_id,
                settings.oss_access_key_secret,
            )

        return self._auth

    @property
    def bucket(self) -> Optional[oss2.Bucket]:
        """获取 OSS Bucket 对象（懒加载）"""
        if not self._enabled or not self.auth:
            return None

        if self._bucket is None:
            self._bucket = oss2.Bucket(
                self.auth,
                settings.oss_endpoint,
                settings.oss_bucket,
            )

        return self._bucket

    @property
    def enabled(self) -> bool:
        """OSS 是否启用"""
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
            raise Exception("OSS 服务未启用，请检查配置")

        try:
            # 上传到 OSS
            result = self.bucket.put_object(
                key=key,
                data=data,
                headers={"Content-Type": content_type},
            )

            # 构建访问 URL
            # 使用 HTTPS 协议，根据 endpoint 构建 URL
            # endpoint 格式通常为: https://oss-{region}.aliyuncs.com
            if settings.oss_endpoint.startswith("https://"):
                base_url = settings.oss_endpoint
            elif settings.oss_endpoint.startswith("http://"):
                base_url = settings.oss_endpoint
            else:
                # 如果没有协议，使用 HTTPS
                base_url = f"https://{settings.oss_endpoint}"

            # 构建 URL: {endpoint}/{bucket}/{key}
            # 或使用自定义域名: {custom_domain}/{key}
            url = f"{base_url}/{settings.oss_bucket}/{key}"

            logger.info(f"OSS 上传成功: {key}")
            return url

        except Exception as e:
            logger.error(f"OSS 上传失败: {e}")
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
            raise Exception("OSS 服务未启用，请检查配置")

        try:
            # 上传文件到 OSS
            with open(file_path, "rb") as file_obj:
                result = self.bucket.put_object(
                    key=key,
                    data=file_obj,
                )

            # 构建访问 URL
            if settings.oss_endpoint.startswith("https://"):
                base_url = settings.oss_endpoint
            elif settings.oss_endpoint.startswith("http://"):
                base_url = settings.oss_endpoint
            else:
                base_url = f"https://{settings.oss_endpoint}"

            url = f"{base_url}/{settings.oss_bucket}/{key}"
            logger.info(f"OSS 文件上传成功: {key}")
            return url

        except Exception as e:
            logger.error(f"OSS 文件上传失败: {e}")
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
        if not self.enabled or not self.bucket:
            raise Exception("OSS 服务未启用，请检查配置")

        try:
            url = self.bucket.sign_url(
                method="GET",
                key=key,
                expires=expires,
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
        if not self.enabled or not self.bucket:
            return False

        try:
            self.bucket.delete_object(key)
            logger.info(f"OSS 对象删除成功: {key}")
            return True

        except Exception as e:
            logger.error(f"OSS 对象删除失败: {e}")
            return False


# 单例实例
oss_service = OssService()
