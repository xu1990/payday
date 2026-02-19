"""测试阿里云OSS存储服务"""
import pytest
from unittest.mock import Mock, patch

from app.utils.oss import OssService


class TestOssService:
    """测试OSS服务"""

    def test_initialization(self):
        """测试初始化"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': "test_key_id",
                'oss_access_key_secret': "test_secret",
                'oss_bucket': "test_bucket",
                'oss_endpoint': "oss-cn-hangzhou.aliyuncs.com"
            })

            service = OssService()

            assert service.enabled is True

    def test_disabled_when_no_config(self):
        """测试配置缺失时服务禁用"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': None,
                'oss_access_key_secret': None,
                'oss_bucket': None,
                'oss_endpoint': None
            })

            service = OssService()

            assert service.enabled is False

    def test_auth_property_lazy_loading(self):
        """测试认证对象懒加载"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': "test_key_id",
                'oss_access_key_secret': "test_secret",
                'oss_bucket': "test_bucket",
                'oss_endpoint': "oss-cn-hangzhou.aliyuncs.com"
            })

            service = OssService()

            # 第一次访问时auth应该为None
            assert service._auth is None

            # 访问auth属性应该初始化认证
            with patch('app.utils.oss.oss2.Auth') as mock_auth_class:
                mock_auth = Mock()
                mock_auth_class.return_value = mock_auth

                auth = service.auth
                assert auth is not None

    def test_bucket_property_lazy_loading(self):
        """测试bucket对象懒加载"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': "test_key_id",
                'oss_access_key_secret': "test_secret",
                'oss_bucket': "test_bucket",
                'oss_endpoint': "oss-cn-hangzhou.aliyuncs.com"
            })

            service = OssService()

            # 访问bucket需要auth先初始化
            with patch('app.utils.oss.oss2.Auth') as mock_auth_class:
                mock_auth = Mock()
                mock_auth_class.return_value = mock_auth
                service._auth = mock_auth

            # 第一次访问时bucket应该为None
            assert service._bucket is None

            # 访问bucket属性应该初始化bucket
            with patch('app.utils.oss.oss2.Bucket') as mock_bucket_class:
                mock_bucket = Mock()
                mock_bucket_class.return_value = mock_bucket

                bucket = service.bucket
                assert bucket is not None

    def test_auth_returns_none_when_disabled(self):
        """测试禁用时返回None"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': None,
                'oss_access_key_secret': None,
                'oss_bucket': None,
                'oss_endpoint': None
            })

            service = OssService()

            assert service.auth is None

    def test_bucket_returns_none_when_disabled(self):
        """测试禁用时返回None"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': None,
                'oss_access_key_secret': None,
                'oss_bucket': None,
                'oss_endpoint': None
            })

            service = OssService()

            assert service.bucket is None


class TestGenerateKey:
    """测试生成对象键"""

    def test_generate_key_default_prefix(self):
        """测试默认前缀"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': "test_key_id",
                'oss_access_key_secret': "test_secret",
                'oss_bucket': "test_bucket",
                'oss_endpoint': "oss-cn-hangzhou.aliyuncs.com"
            })

            service = OssService()
            key = service.generate_key()

            # 应该是 images/YYYY/MM/DD/uuid.jpg 格式
            assert key.startswith("images/")
            assert key.endswith(".jpg")
            assert "/" in key  # 包含日期路径

    def test_generate_key_custom_prefix(self):
        """测试自定义前缀"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': "test_key_id",
                'oss_access_key_secret': "test_secret",
                'oss_bucket': "test_bucket",
                'oss_endpoint': "oss-cn-hangzhou.aliyuncs.com"
            })

            service = OssService()
            key = service.generate_key(prefix="avatars", ext="png")

            assert key.startswith("avatars/")
            assert key.endswith(".png")

    def test_generate_key_different_extensions(self):
        """测试不同文件扩展名"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': "test_key_id",
                'oss_access_key_secret': "test_secret",
                'oss_bucket': "test_bucket",
                'oss_endpoint': "oss-cn-hangzhou.aliyuncs.com"
            })

            service = OssService()

            png_key = service.generate_key(ext="png")
            assert png_key.endswith(".png")

            jpeg_key = service.generate_key(ext="jpeg")
            assert jpeg_key.endswith(".jpeg")

            webp_key = service.generate_key(ext="webp")
            assert webp_key.endswith(".webp")


class TestUploadBytes:
    """测试上传二进制数据"""

    @pytest.mark.asyncio
    async def test_upload_bytes_success(self):
        """测试成功上传"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': "test_key_id",
                'oss_access_key_secret': "test_secret",
                'oss_bucket': "test-bucket",
                'oss_endpoint': "oss-cn-hangzhou.aliyuncs.com"
            })

            service = OssService()

            # Mock OSS认证和bucket
            mock_auth = Mock()
            mock_bucket = Mock()
            mock_bucket.put_object = Mock(return_value=Mock(result=True))
            service._auth = mock_auth
            service._bucket = mock_bucket

            data = b"test image data"
            key = "images/test.jpg"

            url = await service.upload_bytes(data, key)

            # 验证put_object被调用
            mock_bucket.put_object.assert_called_once()

            # 验证返回URL
            assert "test-bucket" in url
            assert key in url

    @pytest.mark.asyncio
    async def test_upload_bytes_when_disabled(self):
        """测试禁用时上传抛出异常"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': None,
                'oss_access_key_secret': None,
                'oss_bucket': None,
                'oss_endpoint': None
            })

            service = OssService()

            with pytest.raises(Exception) as exc_info:
                await service.upload_bytes(b"data", "key.jpg")

            assert "OSS 服务未启用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_bytes_with_custom_content_type(self):
        """测试自定义内容类型"""
        with patch('app.utils.oss.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'oss_access_key_id': "test_key_id",
                'oss_access_key_secret': "test_secret",
                'oss_bucket': "test-bucket",
                'oss_endpoint': "oss-cn-hangzhou.aliyuncs.com"
            })

            service = OssService()

            # Mock OSS认证和bucket
            mock_auth = Mock()
            mock_bucket = Mock()
            mock_bucket.put_object = Mock()
            service._auth = mock_auth
            service._bucket = mock_bucket

            data = b"pdf data"
            key = "docs/test.pdf"

            url = await service.upload_bytes(data, key, content_type="application/pdf")

            # 验证put_object被调用
            mock_bucket.put_object.assert_called_once()
