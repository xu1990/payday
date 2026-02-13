"""
单元测试 - 腾讯云天御内容安全服务 (app.utils.tencent_yu)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

from app.utils.tencent_yu import TencentYuService


class TestTencentYuServiceInit:
    """测试腾讯云天御服务初始化"""

    @pytest.fixture
    def mock_settings_no_creds(self):
        """Mock settings without credentials"""
        with patch('app.utils.tencent_yu.settings') as mock:
            mock.tencent_secret_id = None
            mock.tencent_secret_key = None
            mock.TENCENT_REGION = "ap-guangzhou"
            yield mock

    @pytest.fixture
    def mock_settings_with_creds(self):
        """Mock settings with credentials"""
        with patch('app.utils.tencent_yu.settings') as mock:
            mock.tencent_secret_id = "test_secret_id"
            mock.tencent_secret_key = "test_secret_key"
            mock.TENCENT_REGION = "ap-guangzhou"
            yield mock

    def test_init_without_credentials(self, mock_settings_no_creds):
        """测试无密钥时的初始化"""
        service = TencentYuService()

        assert service.enabled is False
        assert service.ims_client is None
        assert service.tms_client is None
        assert service.ocr_client is None

    def test_init_with_partial_credentials(self):
        """测试部分密钥时的初始化"""
        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.tencent_secret_id = "secret_id"
            mock_settings.tencent_secret_key = None
            mock_settings.TENCENT_REGION = "ap-guangzhou"

            service = TencentYuService()

            assert service.enabled is False

    def test_init_with_credentials_failure(self):
        """测试有密钥但初始化失败"""
        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.tencent_secret_id = "secret_id"
            mock_settings.tencent_secret_key = "secret_key"
            mock_settings.TENCENT_REGION = "ap-guangzhou"

            with patch('app.utils.tencent_yu.credential.Credential', side_effect=Exception("Init failed")):
                service = TencentYuService()

                assert service.enabled is False
                assert service.ims_client is None


class TestImageModeration:
    """测试图片审核功能"""

    @pytest.fixture
    def enabled_service(self):
        """Create an enabled service for testing"""
        service = TencentYuService()
        service._enabled = True
        service.ims_client = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_image_moderation_disabled(self):
        """测试服务未启用时返回通过"""
        service = TencentYuService()
        service._enabled = False

        result = await service.image_moderation("http://example.com/image.jpg")

        assert result["suggestion"] == "pass"
        assert result["labels"] == []
        assert result["porn"] is False

    @pytest.mark.asyncio
    async def test_image_moderation_pass(self, enabled_service):
        """测试审核通过"""
        mock_resp = MagicMock()
        mock_resp.Suggestion = "pass"
        mock_resp.Labels = []

        enabled_service.ims_client.ImageModeration = MagicMock(return_value=mock_resp)

        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.TENCENT_YU_BIZ_TYPE = "payday_risk_check"
            result = await enabled_service.image_moderation("http://example.com/image.jpg")

        assert result["suggestion"] == "pass"
        assert result["porn"] is False
        assert result["violence"] is False

    @pytest.mark.asyncio
    async def test_image_moderation_block_with_labels(self, enabled_service):
        """测试审核拒绝"""
        mock_resp = MagicMock()
        mock_resp.Suggestion = "block"
        mock_resp.Labels = ["Porn", "Violence"]

        enabled_service.ims_client.ImageModeration = MagicMock(return_value=mock_resp)

        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.TENCENT_YU_BIZ_TYPE = "payday_risk_check"
            result = await enabled_service.image_moderation("http://example.com/image.jpg")

        assert result["suggestion"] == "block"
        assert result["porn"] is True
        assert result["violence"] is True
        assert result["ad"] is False

    @pytest.mark.asyncio
    async def test_image_moderation_review(self, enabled_service):
        """测试需要人工审核"""
        mock_resp = MagicMock()
        mock_resp.Suggestion = "review"
        mock_resp.Labels = ["Politics"]

        enabled_service.ims_client.ImageModeration = MagicMock(return_value=mock_resp)

        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.TENCENT_YU_BIZ_TYPE = "payday_risk_check"
            result = await enabled_service.image_moderation("http://example.com/image.jpg")

        assert result["suggestion"] == "review"

    @pytest.mark.asyncio
    async def test_image_moderation_sdk_exception(self, enabled_service):
        """测试腾讯云SDK异常"""
        enabled_service.ims_client.ImageModeration = MagicMock(
            side_effect=TencentCloudSDKException("Test error")
        )

        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.TENCENT_YU_BIZ_TYPE = "payday_risk_check"
            result = await enabled_service.image_moderation("http://example.com/image.jpg")

        # SDK异常应该降级到人工审核
        assert result["suggestion"] == "review"

    @pytest.mark.asyncio
    async def test_image_moderation_generic_exception(self, enabled_service):
        """测试通用异常"""
        enabled_service.ims_client.ImageModeration = MagicMock(
            side_effect=Exception("Generic error")
        )

        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.TENCENT_YU_BIZ_TYPE = "payday_risk_check"
            result = await enabled_service.image_moderation("http://example.com/image.jpg")

        assert result["suggestion"] == "review"


class TestTextModeration:
    """测试文本审核功能"""

    @pytest.fixture
    def enabled_service(self):
        """Create an enabled service for testing"""
        service = TencentYuService()
        service._enabled = True
        service.tms_client = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_text_moderation_disabled(self):
        """测试服务未启用时返回通过"""
        service = TencentYuService()
        service._enabled = False

        result = await service.text_moderation("测试文本")

        assert result["suggestion"] == "pass"
        assert result["labels"] == []

    @pytest.mark.asyncio
    async def test_text_moderation_pass(self, enabled_service):
        """测试文本审核通过"""
        mock_resp = MagicMock()
        mock_resp.Suggestion = "pass"
        mock_resp.Labels = []
        mock_resp.DetailResults = []

        enabled_service.tms_client.TextModeration = MagicMock(return_value=mock_resp)

        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.TENCENT_YU_BIZ_TYPE = "payday_risk_check"
            result = await enabled_service.text_moderation("这是正常文本")

        assert result["suggestion"] == "pass"
        assert result["labels"] == []

    @pytest.mark.asyncio
    async def test_text_moderation_block(self, enabled_service):
        """测试文本审核拒绝"""
        mock_resp = MagicMock()
        mock_resp.Suggestion = "block"
        mock_resp.Labels = ["Spam", "Porn"]
        mock_resp.DetailResults = []

        enabled_service.tms_client.TextModeration = MagicMock(return_value=mock_resp)

        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.TENCENT_YU_BIZ_TYPE = "payday_risk_check"
            result = await enabled_service.text_moderation("违规文本内容")

        assert result["suggestion"] == "block"
        assert "Spam" in result["labels"]

    @pytest.mark.asyncio
    async def test_text_moderation_exception(self, enabled_service):
        """测试文本审核异常"""
        enabled_service.tms_client.TextModeration = MagicMock(
            side_effect=TencentCloudSDKException("Text moderation error")
        )

        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.TENCENT_YU_BIZ_TYPE = "payday_risk_check"
            result = await enabled_service.text_moderation("测试文本")

        assert result["suggestion"] == "review"


class TestOcrExtractText:
    """测试OCR文字提取功能"""

    @pytest.fixture
    def enabled_service(self):
        """Create an enabled service for testing"""
        service = TencentYuService()
        service._enabled = True
        service.ocr_client = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_ocr_disabled(self):
        """测试服务未启用时返回None"""
        service = TencentYuService()
        service._enabled = False

        result = await service.ocr_extract_text("http://example.com/image.jpg")

        assert result is None

    @pytest.mark.asyncio
    async def test_ocr_success(self, enabled_service):
        """测试OCR提取成功"""
        # Mock OCR response
        mock_detection = MagicMock()
        mock_detection.DetectedText = "第一行文字"

        mock_resp = MagicMock()
        mock_resp.TextDetections = [mock_detection]

        enabled_service.ocr_client.GeneralBasicOCR = MagicMock(return_value=mock_resp)

        result = await enabled_service.ocr_extract_text("http://example.com/image.jpg")

        assert result == "第一行文字"

    @pytest.mark.asyncio
    async def test_ocr_multiple_lines(self, enabled_service):
        """测试OCR提取多行文字"""
        # Mock OCR response with multiple detections
        mock_detection1 = MagicMock()
        mock_detection1.DetectedText = "第一行"

        mock_detection2 = MagicMock()
        mock_detection2.DetectedText = "第二行"

        mock_detection3 = MagicMock()
        mock_detection3.DetectedText = "第三行"

        mock_resp = MagicMock()
        mock_resp.TextDetections = [mock_detection1, mock_detection2, mock_detection3]

        enabled_service.ocr_client.GeneralBasicOCR = MagicMock(return_value=mock_resp)

        result = await enabled_service.ocr_extract_text("http://example.com/image.jpg")

        assert result == "第一行\n第二行\n第三行"

    @pytest.mark.asyncio
    async def test_ocr_no_detections(self, enabled_service):
        """测试OCR没有检测到文字"""
        mock_resp = MagicMock()
        mock_resp.TextDetections = []

        enabled_service.ocr_client.GeneralBasicOCR = MagicMock(return_value=mock_resp)

        result = await enabled_service.ocr_extract_text("http://example.com/image.jpg")

        assert result is None

    @pytest.mark.asyncio
    async def test_ocr_sdk_exception(self, enabled_service):
        """测试OCR SDK异常"""
        enabled_service.ocr_client.GeneralBasicOCR = MagicMock(
            side_effect=TencentCloudSDKException("OCR failed")
        )

        result = await enabled_service.ocr_extract_text("http://example.com/image.jpg")

        assert result is None

    @pytest.mark.asyncio
    async def test_ocr_generic_exception(self, enabled_service):
        """测试OCR通用异常"""
        enabled_service.ocr_client.GeneralBasicOCR = MagicMock(
            side_effect=Exception("Generic OCR error")
        )

        result = await enabled_service.ocr_extract_text("http://example.com/image.jpg")

        assert result is None


class TestBatchImageModeration:
    """测试批量图片审核"""

    @pytest.fixture
    def enabled_service(self):
        """Create an enabled service for testing"""
        service = TencentYuService()
        service._enabled = True
        service.ims_client = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_batch_moderation(self, enabled_service):
        """测试批量审核"""
        # Mock responses
        mock_resp_pass = MagicMock()
        mock_resp_pass.Suggestion = "pass"
        mock_resp_pass.Labels = []

        mock_resp_block = MagicMock()
        mock_resp_block.Suggestion = "block"
        mock_resp_block.Labels = ["Porn"]

        enabled_service.ims_client.ImageModeration = MagicMock(
            side_effect=[mock_resp_pass, mock_resp_block]
        )

        with patch('app.utils.tencent_yu.settings') as mock_settings:
            mock_settings.TENCENT_YU_BIZ_TYPE = "payday_risk_check"
            results = await enabled_service.batch_image_moderation([
                "http://example.com/image1.jpg",
                "http://example.com/image2.jpg",
            ])

        assert len(results) == 2
        assert results[0]["suggestion"] == "pass"
        assert results[1]["suggestion"] == "block"

    @pytest.mark.asyncio
    async def test_batch_moderation_empty_list(self, enabled_service):
        """测试空列表批量审核"""
        results = await enabled_service.batch_image_moderation([])

        assert results == []


class TestHelperFunctions:
    """测试辅助函数"""

    @pytest.mark.asyncio
    async def test_image_check_pass(self):
        """测试图片审核通过"""
        # Mock the singleton service
        mock_service = MagicMock()
        mock_service.image_moderation = AsyncMock(return_value={
            "suggestion": "pass",
            "porn": False,
            "violence": False,
            "ad": False,
        })

        with patch('app.utils.tencent_yu.tencent_yu_service', mock_service):
            from app.utils.tencent_yu import tencent_yu_image_check

            score, reason = await tencent_yu_image_check("http://example.com/image.jpg")

            assert score == 0
            assert reason is None

    @pytest.mark.asyncio
    async def test_image_check_review(self):
        """测试图片需要人工审核"""
        mock_service = MagicMock()
        mock_service.image_moderation = AsyncMock(return_value={
            "suggestion": "review",
            "porn": False,
            "violence": False,
            "ad": False,
        })

        with patch('app.utils.tencent_yu.tencent_yu_service', mock_service):
            from app.utils.tencent_yu import tencent_yu_image_check

            score, reason = await tencent_yu_image_check("http://example.com/image.jpg")

            assert score == 50
            assert reason == "图片需要人工审核"

    @pytest.mark.asyncio
    async def test_image_check_block_single_reason(self):
        """测试图片拒绝 - 单个原因"""
        mock_service = MagicMock()
        mock_service.image_moderation = AsyncMock(return_value={
            "suggestion": "block",
            "porn": True,
            "violence": False,
            "ad": False,
        })

        with patch('app.utils.tencent_yu.tencent_yu_service', mock_service):
            from app.utils.tencent_yu import tencent_yu_image_check

            score, reason = await tencent_yu_image_check("http://example.com/image.jpg")

            assert score == 90
            assert "色情" in reason

    @pytest.mark.asyncio
    async def test_image_check_block_multiple_reasons(self):
        """测试图片拒绝 - 多个原因"""
        mock_service = MagicMock()
        mock_service.image_moderation = AsyncMock(return_value={
            "suggestion": "block",
            "porn": True,
            "violence": True,
            "ad": True,
        })

        with patch('app.utils.tencent_yu.tencent_yu_service', mock_service):
            from app.utils.tencent_yu import tencent_yu_image_check

            score, reason = await tencent_yu_image_check("http://example.com/image.jpg")

            assert score == 90
            assert "色情" in reason
            assert "暴力" in reason
            assert "广告" in reason

    @pytest.mark.asyncio
    async def test_text_check_pass(self):
        """测试文本审核通过"""
        mock_service = MagicMock()
        mock_service.text_moderation = AsyncMock(return_value={
            "suggestion": "pass",
            "labels": [],
            "details": [],
        })

        with patch('app.utils.tencent_yu.tencent_yu_service', mock_service):
            from app.utils.tencent_yu import tencent_yu_text_check

            score, reason = await tencent_yu_text_check("正常文本")

            assert score == 0
            assert reason is None

    @pytest.mark.asyncio
    async def test_text_check_review(self):
        """测试文本需要人工审核"""
        mock_service = MagicMock()
        mock_service.text_moderation = AsyncMock(return_value={
            "suggestion": "review",
            "labels": [],
            "details": [],
        })

        with patch('app.utils.tencent_yu.tencent_yu_service', mock_service):
            from app.utils.tencent_yu import tencent_yu_text_check

            score, reason = await tencent_yu_text_check("可疑文本")

            assert score == 50
            assert reason == "文本需要人工审核"

    @pytest.mark.asyncio
    async def test_text_check_block(self):
        """测试文本拒绝"""
        mock_service = MagicMock()
        mock_service.text_moderation = AsyncMock(return_value={
            "suggestion": "block",
            "labels": ["Spam", "Porn"],
            "details": [],
        })

        with patch('app.utils.tencent_yu.tencent_yu_service', mock_service):
            from app.utils.tencent_yu import tencent_yu_text_check

            score, reason = await tencent_yu_text_check("违规文本")

            assert score == 90
            assert "Spam" in reason
            assert "Porn" in reason
