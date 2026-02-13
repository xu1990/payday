"""
单元测试 - 统一存储服务 (app.utils.storage)
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.utils.storage import UnifiedStorageService


class TestUnifiedStorageServiceInit:
    """测试 UnifiedStorageService 初始化"""

    @patch('app.utils.storage.settings')
    def test_init_with_cos_provider(self, mock_settings):
        """测试使用 COS 提供商初始化"""
        mock_settings.storage_provider = "cos"

        service = UnifiedStorageService()

        assert service._provider == "cos"

    @patch('app.utils.storage.settings')
    def test_init_with_oss_provider(self, mock_settings):
        """测试使用 OSS 提供商初始化"""
        mock_settings.storage_provider = "oss"

        service = UnifiedStorageService()

        assert service._provider == "oss"

    @patch('app.utils.storage.settings')
    def test_init_with_invalid_provider(self, mock_settings):
        """测试使用无效提供商初始化"""
        mock_settings.storage_provider = "invalid"

        service = UnifiedStorageService()

        # Should default to cos
        assert service._provider == "cos"

    @patch('app.utils.storage.settings')
    def test_init_case_insensitive(self, mock_settings):
        """测试提供商名称不区分大小写"""
        mock_settings.storage_provider = "COS"

        service = UnifiedStorageService()

        assert service._provider == "cos"


class TestValidateProvider:
    """测试提供商验证"""

    @patch('app.utils.storage.settings')
    def test_validate_cos_provider(self, mock_settings):
        """测试验证 COS 提供商"""
        mock_settings.storage_provider = "cos"

        service = UnifiedStorageService()
        service._validate_provider()

        assert service._provider == "cos"

    @patch('app.utils.storage.settings')
    def test_validate_oss_provider(self, mock_settings):
        """测试验证 OSS 提供商"""
        mock_settings.storage_provider = "oss"

        service = UnifiedStorageService()
        service._validate_provider()

        assert service._provider == "oss"

    @patch('app.utils.storage.settings')
    def test_validate_invalid_provider_defaults_to_cos(self, mock_settings):
        """测试无效提供商默认使用 COS"""
        mock_settings.storage_provider = "s3"

        service = UnifiedStorageService()
        service._validate_provider()

        assert service._provider == "cos"


class TestProperties:
    """测试属性方法"""

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_cos_enabled_property(self, mock_oss, mock_cos, mock_settings):
        """测试 cos_enabled 属性"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = True
        mock_oss.enabled = False

        service = UnifiedStorageService()

        assert service.cos_enabled is True
        assert service.oss_enabled is False

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_oss_enabled_property(self, mock_oss, mock_cos, mock_settings):
        """测试 oss_enabled 属性"""
        mock_settings.storage_provider = "oss"
        mock_cos.enabled = False
        mock_oss.enabled = True

        service = UnifiedStorageService()

        assert service.cos_enabled is False
        assert service.oss_enabled is True

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_enabled_property_when_cos_active(self, mock_oss, mock_cos, mock_settings):
        """测试当 COS 启用时的 enabled 属性"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = True
        mock_oss.enabled = False

        service = UnifiedStorageService()

        assert service.enabled is True

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_enabled_property_when_both_disabled(self, mock_oss, mock_cos, mock_settings):
        """测试两个服务都禁用时的 enabled 属性"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = False
        mock_oss.enabled = False

        service = UnifiedStorageService()

        assert service.enabled is False

    @patch('app.utils.storage.settings')
    def test_current_provider_property(self, mock_settings):
        """测试 current_provider 属性"""
        mock_settings.storage_provider = "oss"

        service = UnifiedStorageService()

        assert service.current_provider == "oss"


class TestGenerateKey:
    """测试生成对象键"""

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_generate_key_with_cos(self, mock_oss, mock_cos, mock_settings):
        """测试使用 COS 生成键"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = True
        mock_oss.enabled = False
        mock_cos.generate_key.return_value = "images/2024/01/test.jpg"
        mock_oss.generate_key.return_value = "oss/images/test.jpg"

        service = UnifiedStorageService()
        key = service.generate_key("images", "jpg")

        assert key == "images/2024/01/test.jpg"
        mock_cos.generate_key.assert_called_once_with("images", "jpg")

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_generate_key_with_oss(self, mock_oss, mock_cos, mock_settings):
        """测试使用 OSS 生成键"""
        mock_settings.storage_provider = "oss"
        mock_cos.enabled = False
        mock_oss.enabled = True
        mock_cos.generate_key.return_value = "cos/images/test.jpg"
        mock_oss.generate_key.return_value = "oss/images/test.jpg"

        service = UnifiedStorageService()
        key = service.generate_key("images", "jpg")

        assert key == "oss/images/test.jpg"
        mock_oss.generate_key.assert_called_once_with("images", "jpg")

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_generate_key_defaults_to_cos_when_oss_disabled(self, mock_oss, mock_cos, mock_settings):
        """测试 OSS 禁用时默认使用 COS"""
        mock_settings.storage_provider = "oss"
        mock_cos.enabled = True
        mock_oss.enabled = False
        mock_cos.generate_key.return_value = "cos/images/test.jpg"

        service = UnifiedStorageService()
        key = service.generate_key("images", "jpg")

        assert key == "cos/images/test.jpg"
        mock_cos.generate_key.assert_called_once_with("images", "jpg")


class TestUploadBytes:
    """测试上传二进制数据"""

    @pytest.mark.asyncio
    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    async def test_upload_bytes_with_cos(self, mock_oss, mock_cos, mock_settings):
        """测试使用 COS 上传二进制数据"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = True
        mock_oss.enabled = False
        mock_cos.upload_bytes = AsyncMock(return_value="https://cos.example.com/file.jpg")

        service = UnifiedStorageService()
        url = await service.upload_bytes(b"test data", "test.jpg", "image/jpeg")

        assert url == "https://cos.example.com/file.jpg"
        mock_cos.upload_bytes.assert_called_once_with(b"test data", "test.jpg", "image/jpeg")

    @pytest.mark.asyncio
    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    async def test_upload_bytes_with_oss(self, mock_oss, mock_cos, mock_settings):
        """测试使用 OSS 上传二进制数据"""
        mock_settings.storage_provider = "oss"
        mock_cos.enabled = False
        mock_oss.enabled = True
        mock_oss.upload_bytes = AsyncMock(return_value="https://oss.example.com/file.jpg")

        service = UnifiedStorageService()
        url = await service.upload_bytes(b"test data", "test.jpg", "image/jpeg")

        assert url == "https://oss.example.com/file.jpg"
        mock_oss.upload_bytes.assert_called_once_with(b"test data", "test.jpg", "image/jpeg")

    @pytest.mark.asyncio
    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    async def test_upload_bytes_when_disabled(self, mock_oss, mock_cos, mock_settings):
        """测试服务禁用时上传"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = False
        mock_oss.enabled = False

        service = UnifiedStorageService()

        with pytest.raises(Exception) as exc_info:
            await service.upload_bytes(b"test data", "test.jpg")

        assert "存储服务未启用" in str(exc_info.value)


class TestUploadFile:
    """测试上传本地文件"""

    @pytest.mark.asyncio
    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    async def test_upload_file_with_cos(self, mock_oss, mock_cos, mock_settings):
        """测试使用 COS 上传本地文件"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = True
        mock_oss.enabled = False
        mock_cos.upload_file = AsyncMock(return_value="https://cos.example.com/file.jpg")

        service = UnifiedStorageService()
        url = await service.upload_file("/local/path/file.jpg", "test.jpg")

        assert url == "https://cos.example.com/file.jpg"
        mock_cos.upload_file.assert_called_once_with("/local/path/file.jpg", "test.jpg")

    @pytest.mark.asyncio
    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    async def test_upload_file_with_oss(self, mock_oss, mock_cos, mock_settings):
        """测试使用 OSS 上传本地文件"""
        mock_settings.storage_provider = "oss"
        mock_cos.enabled = False
        mock_oss.enabled = True
        mock_oss.upload_file = AsyncMock(return_value="https://oss.example.com/file.jpg")

        service = UnifiedStorageService()
        url = await service.upload_file("/local/path/file.jpg", "test.jpg")

        assert url == "https://oss.example.com/file.jpg"
        mock_oss.upload_file.assert_called_once_with("/local/path/file.jpg", "test.jpg")

    @pytest.mark.asyncio
    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    async def test_upload_file_when_disabled(self, mock_oss, mock_cos, mock_settings):
        """测试服务禁用时上传文件"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = False
        mock_oss.enabled = False

        service = UnifiedStorageService()

        with pytest.raises(Exception) as exc_info:
            await service.upload_file("/local/path/file.jpg", "test.jpg")

        assert "存储服务未启用" in str(exc_info.value)


class TestGetPresignedUrl:
    """测试获取预签名 URL"""

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_get_presigned_url_with_cos(self, mock_oss, mock_cos, mock_settings):
        """测试使用 COS 获取预签名 URL"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = True
        mock_oss.enabled = False
        mock_cos.get_presigned_url.return_value = "https://cos.example.com/signed-url"

        service = UnifiedStorageService()
        url = service.get_presigned_url("test.jpg", 3600)

        assert url == "https://cos.example.com/signed-url"
        mock_cos.get_presigned_url.assert_called_once_with("test.jpg", 3600)

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_get_presigned_url_with_oss(self, mock_oss, mock_cos, mock_settings):
        """测试使用 OSS 获取预签名 URL"""
        mock_settings.storage_provider = "oss"
        mock_cos.enabled = False
        mock_oss.enabled = True
        mock_oss.get_presigned_url.return_value = "https://oss.example.com/signed-url"

        service = UnifiedStorageService()
        url = service.get_presigned_url("test.jpg", 1800)

        assert url == "https://oss.example.com/signed-url"
        mock_oss.get_presigned_url.assert_called_once_with("test.jpg", 1800)

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_get_presigned_url_when_disabled(self, mock_oss, mock_cos, mock_settings):
        """测试服务禁用时获取预签名 URL"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = False
        mock_oss.enabled = False

        service = UnifiedStorageService()

        with pytest.raises(Exception) as exc_info:
            service.get_presigned_url("test.jpg")

        assert "存储服务未启用" in str(exc_info.value)


class TestDeleteObject:
    """测试删除对象"""

    @pytest.mark.asyncio
    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    async def test_delete_object_with_cos(self, mock_oss, mock_cos, mock_settings):
        """测试使用 COS 删除对象"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = True
        mock_oss.enabled = False
        mock_cos.delete_object = AsyncMock(return_value=True)

        service = UnifiedStorageService()
        result = await service.delete_object("test.jpg")

        assert result is True
        mock_cos.delete_object.assert_called_once_with("test.jpg")

    @pytest.mark.asyncio
    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    async def test_delete_object_with_oss(self, mock_oss, mock_cos, mock_settings):
        """测试使用 OSS 删除对象"""
        mock_settings.storage_provider = "oss"
        mock_cos.enabled = False
        mock_oss.enabled = True
        mock_oss.delete_object = AsyncMock(return_value=True)

        service = UnifiedStorageService()
        result = await service.delete_object("test.jpg")

        assert result is True
        mock_oss.delete_object.assert_called_once_with("test.jpg")

    @pytest.mark.asyncio
    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    async def test_delete_object_when_disabled(self, mock_oss, mock_cos, mock_settings):
        """测试服务禁用时删除对象"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = False
        mock_oss.enabled = False

        service = UnifiedStorageService()
        result = await service.delete_object("test.jpg")

        assert result is False


class TestGetStatus:
    """测试获取服务状态"""

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_get_status_with_cos(self, mock_oss, mock_cos, mock_settings):
        """测试获取 COS 状态"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = True
        mock_oss.enabled = False

        service = UnifiedStorageService()
        status = service.get_status()

        assert status["provider"] == "cos"
        assert status["cos_enabled"] is True
        assert status["oss_enabled"] is False
        assert status["current_service"] == "腾讯云 COS"
        assert status["healthy"] is True

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_get_status_with_oss(self, mock_oss, mock_cos, mock_settings):
        """测试获取 OSS 状态"""
        mock_settings.storage_provider = "oss"
        mock_cos.enabled = False
        mock_oss.enabled = True

        service = UnifiedStorageService()
        status = service.get_status()

        assert status["provider"] == "oss"
        assert status["cos_enabled"] is False
        assert status["oss_enabled"] is True
        assert status["current_service"] == "阿里云 OSS"
        assert status["healthy"] is True

    @patch('app.utils.storage.settings')
    @patch('app.utils.storage._cos_service')
    @patch('app.utils.storage._oss_service')
    def test_get_status_when_both_disabled(self, mock_oss, mock_cos, mock_settings):
        """测试两个服务都禁用时的状态"""
        mock_settings.storage_provider = "cos"
        mock_cos.enabled = False
        mock_oss.enabled = False

        service = UnifiedStorageService()
        status = service.get_status()

        assert status["healthy"] is False
