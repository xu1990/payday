"""测试腾讯云COS存储服务"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.utils.cos import CosService


class TestCosService:
    """测试COS服务"""

    def test_initialization(self):
        """测试初始化"""
        with patch('app.utils.cos.settings') as mock_settings:
            mock_config = Mock()
            mock_config.cos_secret_id = "test_secret_id"
            mock_config.cos_secret_key = "test_secret_key"
            mock_config.cos_bucket = "test_bucket"
            mock_config.cos_region = "ap-guangzhou"
            mock_settings.configure_mock(**{
                'cos_secret_id': "test_secret_id",
                'cos_secret_key': "test_secret_key",
                'cos_bucket': "test_bucket",
                'cos_region': "ap-guangzhou"
            })

            service = CosService()

            assert service.enabled is True

    def test_disabled_when_no_config(self):
        """测试配置缺失时服务禁用"""
        with patch('app.utils.cos.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'cos_secret_id': None,
                'cos_secret_key': None,
                'cos_bucket': None
            })

            service = CosService()

            assert service.enabled is False

    def test_client_property_lazy_loading(self):
        """测试客户端懒加载"""
        with patch('app.utils.cos.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'cos_secret_id': "test_id",
                'cos_secret_key': "test_key",
                'cos_bucket': "test_bucket",
                'cos_region': "ap-guangzhou"
            })

            service = CosService()

            # 第一次访问时client应该为None
            assert service._client is None

            # 访问client属性应该初始化客户端
            with patch('app.utils.cos.CosS3Client') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client

                client = service.client
                assert client is not None

    def test_client_returns_none_when_disabled(self):
        """测试禁用时返回None"""
        with patch('app.utils.cos.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'cos_secret_id': None,
                'cos_secret_key': None,
                'cos_bucket': None
            })

            service = CosService()

            assert service.client is None


class TestGenerateKey:
    """测试生成对象键"""

    def test_generate_key_default_prefix(self):
        """测试默认前缀"""
        with patch('app.utils.cos.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'cos_secret_id': "test_id",
                'cos_secret_key': "test_key",
                'cos_bucket': "test_bucket",
                'cos_region': "ap-guangzhou"
            })

            service = CosService()
            key = service.generate_key()

            # 应该是 images/YYYY/MM/DD/uuid.jpg 格式
            assert key.startswith("images/")
            assert key.endswith(".jpg")
            assert "/" in key  # 包含日期路径

    def test_generate_key_custom_prefix(self):
        """测试自定义前缀"""
        with patch('app.utils.cos.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'cos_secret_id': "test_id",
                'cos_secret_key': "test_key",
                'cos_bucket': "test_bucket",
                'cos_region': "ap-guangzhou"
            })

            service = CosService()
            key = service.generate_key(prefix="documents", ext="pdf")

            assert key.startswith("documents/")
            assert key.endswith(".pdf")

    def test_generate_key_different_extensions(self):
        """测试不同文件扩展名"""
        with patch('app.utils.cos.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'cos_secret_id': "test_id",
                'cos_secret_key': "test_key",
                'cos_bucket': "test_bucket",
                'cos_region': "ap-guangzhou"
            })

            service = CosService()

            png_key = service.generate_key(ext="png")
            assert png_key.endswith(".png")

            gif_key = service.generate_key(ext="gif")
            assert gif_key.endswith(".gif")

            txt_key = service.generate_key(ext="txt")
            assert txt_key.endswith(".txt")


class TestUploadBytes:
    """测试上传二进制数据"""

    @pytest.mark.asyncio
    async def test_upload_bytes_success(self):
        """测试成功上传"""
        with patch('app.utils.cos.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'cos_secret_id': "test_id",
                'cos_secret_key': "test_key",
                'cos_bucket': "test-bucket",
                'cos_region': "ap-guangzhou"
            })

            service = CosService()

            # Mock COS客户端
            mock_cos_client = Mock()
            mock_cos_client.put_object = Mock()
            service._client = mock_cos_client

            data = b"test image data"
            key = "images/test.jpg"

            url = await service.upload_bytes(data, key)

            # 验证put_object被调用
            mock_cos_client.put_object.assert_called_once()

            # 验证返回URL
            assert "test-bucket" in url
            assert key in url

    @pytest.mark.asyncio
    async def test_upload_bytes_when_disabled(self):
        """测试禁用时上传抛出异常"""
        with patch('app.utils.cos.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'cos_secret_id': None,
                'cos_secret_key': None,
                'cos_bucket': None
            })

            service = CosService()

            with pytest.raises(Exception) as exc_info:
                await service.upload_bytes(b"data", "key.jpg")

            assert "COS 服务未启用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_bytes_with_custom_content_type(self):
        """测试自定义内容类型"""
        with patch('app.utils.cos.settings') as mock_settings:
            mock_settings.configure_mock(**{
                'cos_secret_id': "test_id",
                'cos_secret_key': "test_key",
                'cos_bucket': "test-bucket",
                'cos_region': "ap-guangzhou"
            })

            service = CosService()

            # Mock COS客户端
            mock_cos_client = Mock()
            mock_cos_client.put_object = Mock()
            service._client = mock_cos_client

            data = b"pdf data"
            key = "docs/test.pdf"

            url = await service.upload_bytes(data, key, content_type="application/pdf")

            # 验证put_object被调用
            mock_cos_client.put_object.assert_called_once()
            call_args = mock_cos_client.put_object.call_args

            # 检查ContentType参数
            assert call_args[1]["ContentType"] == "application/pdf"
