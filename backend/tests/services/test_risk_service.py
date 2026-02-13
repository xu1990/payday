"""风控服务测试"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.risk_service import (
    _text_contact_score,
    _text_sensitive_score,
    _image_score,
    evaluate_content,
    _text_sensitive_score_from_db,
    RiskResult,
)


class TestTextContactScore:
    """测试联系方式检测"""

    def test_phone_number_detection(self):
        """检测手机号"""
        score, reason = _text_contact_score("联系我：13812345678")
        assert score == 80
        assert reason == "含联系方式或诱导外联"

    def test_email_detection(self):
        """检测邮箱"""
        score, reason = _text_contact_score("邮箱：test@example.com")
        assert score == 80
        assert reason == "含联系方式或诱导外联"

    def test_qq_detection(self):
        """检测QQ号"""
        score, reason = _text_contact_score("我的qq：123456789")
        assert score == 80
        assert reason == "含联系方式或诱导外联"

    def test_wechat_detection(self):
        """检测微信号"""
        score, reason = _text_contact_score("微信：abc123456")
        assert score == 80
        assert reason == "含联系方式或诱导外联"

    def test_no_contact_info(self):
        """无联系方式"""
        score, reason = _text_contact_score("今天天气真好")
        assert score == 0
        assert reason is None

    def test_empty_content(self):
        """空内容"""
        score, reason = _text_contact_score("")
        assert score == 0
        assert reason is None

    def test_whitespace_only(self):
        """仅空白字符"""
        score, reason = _text_contact_score("   \n\t  ")
        assert score == 0
        assert reason is None


class TestTextSensitiveScore:
    """测试敏感词检测（已废弃函数）"""

    def test_deprecated_function(self):
        """测试已废弃的函数返回0"""
        score, reason = _text_sensitive_score("任何内容")
        assert score == 0
        assert reason is None


class TestImageScore:
    """测试图片审核"""

    @pytest.mark.asyncio
    async def test_single_image_pass(self):
        """单张图片通过"""
        with patch('app.services.risk_service.tencent_yu_image_check', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = (0, None)

            score, reason = await _image_score(["https://example.com/image1.jpg"])

            assert score == 0
            assert reason is None
            mock_check.assert_called_once_with("https://example.com/image1.jpg")

    @pytest.mark.asyncio
    async def test_single_image_reject(self):
        """单张图片违规"""
        with patch('app.services.risk_service.tencent_yu_image_check', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = (90, "色情内容")

            score, reason = await _image_score(["https://example.com/bad.jpg"])

            assert score == 90
            assert reason == "色情内容"

    @pytest.mark.asyncio
    async def test_multiple_images_worst_score(self):
        """多张图片取最高分"""
        with patch('app.services.risk_service.tencent_yu_image_check', new_callable=AsyncMock) as mock_check:
            # 模拟不同图片返回不同分数
            mock_check.side_effect = [
                (10, None),
                (80, "违规内容"),
                (30, None),
            ]

            score, reason = await _image_score([
                "https://example.com/img1.jpg",
                "https://example.com/img2.jpg",
                "https://example.com/img3.jpg",
            ])

            # 应该返回最高分
            assert score == 80
            assert reason == "违规内容"

    @pytest.mark.asyncio
    async def test_empty_image_list(self):
        """空图片列表"""
        score, reason = await _image_score(None)
        assert score == 0
        assert reason is None

        score, reason = await _image_score([])
        assert score == 0
        assert reason is None

    @pytest.mark.asyncio
    async def test_image_check_failure_continues(self):
        """单张图片检查失败不影响其他图片"""
        with patch('app.services.risk_service.tencent_yu_image_check', new_callable=AsyncMock) as mock_check:
            # 第一张失败，第二张成功
            mock_check.side_effect = [
                Exception("Network error"),
                (70, "可疑内容"),
            ]

            score, reason = await _image_score([
                "https://example.com/img1.jpg",
                "https://example.com/img2.jpg",
            ])

            # 应该继续处理并返回成功图片的分数
            assert score == 70
            assert reason == "可疑内容"


class TestTextSensitiveScoreFromDb:
    """测试从数据库获取敏感词"""

    @pytest.mark.asyncio
    async def test_sensitive_word_found(self, db_session: AsyncSession):
        """测试检测到敏感词"""
        with patch('app.services.risk_service.sensitive_word_service.get_all_active_words_list', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ["毒品", "赌博"]

            score, reason = await _text_sensitive_score_from_db(db_session, "这是关于毒品的内容")

            assert score == 90
            assert reason == "含违规内容"

    @pytest.mark.asyncio
    async def test_no_sensitive_word(self, db_session: AsyncSession):
        """测试无敏感词"""
        with patch('app.services.risk_service.sensitive_word_service.get_all_active_words_list', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ["毒品", "赌博"]

            score, reason = await _text_sensitive_score_from_db(db_session, "今天天气真好")

            assert score == 0
            assert reason is None

    @pytest.mark.asyncio
    async def test_case_insensitive(self, db_session: AsyncSession):
        """测试大小写不敏感（英文敏感词）"""
        with patch('app.services.risk_service.sensitive_word_service.get_all_active_words_list', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ["drug", "viagra"]

            score, reason = await _text_sensitive_score_from_db(db_session, "This contains DRUG content")

            # 应该检测到（虽然大小写不同）
            assert score == 90

    @pytest.mark.asyncio
    async def test_db_failure_uses_fallback(self, db_session: AsyncSession):
        """测试数据库失败时使用备用敏感词列表"""
        with patch('app.services.risk_service.sensitive_word_service.get_all_active_words_list', new_callable=AsyncMock) as mock_get:
            # 模拟数据库查询失败
            mock_get.side_effect = Exception("DB error")

            # 使用备用列表中的敏感词
            score, reason = await _text_sensitive_score_from_db(db_session, "这是关于毒品的内容")

            assert score == 90
            assert reason == "含违规内容"

    @pytest.mark.asyncio
    async def test_empty_content(self, db_session: AsyncSession):
        """测试空内容"""
        with patch('app.services.risk_service.sensitive_word_service.get_all_active_words_list', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ["毒品"]

            score, reason = await _text_sensitive_score_from_db(db_session, "")

            assert score == 0
            assert reason is None

    @pytest.mark.asyncio
    async def test_whitespace_only(self, db_session: AsyncSession):
        """测试仅空白字符"""
        with patch('app.services.risk_service.sensitive_word_service.get_all_active_words_list', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ["毒品"]

            score, reason = await _text_sensitive_score_from_db(db_session, "   \n\t  ")

            assert score == 0
            assert reason is None


class TestEvaluateContent:
    """测试内容风险评估"""

    @pytest.mark.asyncio
    async def test_clean_text_approve(self, db_session: AsyncSession):
        """测试干净文本通过"""
        with patch('app.services.risk_service._text_sensitive_score_from_db', new_callable=AsyncMock) as mock_sensitive:
            mock_sensitive.return_value = (0, None)

            result = await evaluate_content(db_session, "今天天气真好")

            assert result.action == "approve"
            assert result.score == 0

    @pytest.mark.asyncio
    async def test_sensitive_word_reject(self, db_session: AsyncSession):
        """测试敏感词拒绝"""
        with patch('app.services.risk_service._text_sensitive_score_from_db', new_callable=AsyncMock) as mock_sensitive:
            mock_sensitive.return_value = (90, "含违规内容")

            result = await evaluate_content(db_session, "包含敏感词的内容")

            assert result.action == "reject"
            assert result.score == 90
            assert "含违规内容" in result.reason

    @pytest.mark.asyncio
    async def test_contact_info_reject(self, db_session: AsyncSession):
        """测试联系方式拒绝"""
        with patch('app.services.risk_service._text_sensitive_score_from_db', new_callable=AsyncMock) as mock_sensitive:
            mock_sensitive.return_value = (0, None)

            result = await evaluate_content(db_session, "联系我：13812345678")

            assert result.action == "reject"
            assert result.score == 80

    @pytest.mark.asyncio
    async def test_manual_review(self, db_session: AsyncSession):
        """测试需要人工审核"""
        with patch('app.services.risk_service._text_sensitive_score_from_db', new_callable=AsyncMock) as mock_sensitive:
            mock_sensitive.return_value = (50, "可疑内容")

            result = await evaluate_content(db_session, "可疑内容")

            assert result.action == "manual"
            assert result.score == 50

    @pytest.mark.asyncio
    async def test_without_yu_service(self, db_session: AsyncSession):
        """测试不使用天御服务"""
        with patch('app.services.risk_service._text_sensitive_score_from_db', new_callable=AsyncMock) as mock_sensitive:
            mock_sensitive.return_value = (0, None)

            result = await evaluate_content(db_session, "今天天气真好", use_yu=False)

            # 应该不调用天御服务，直接通过
            assert result.action == "approve"

    @pytest.mark.asyncio
    async def test_with_images_reject(self, db_session: AsyncSession):
        """测试违规图片导致拒绝"""
        with patch('app.services.risk_service._text_sensitive_score_from_db', new_callable=AsyncMock) as mock_sensitive:
            mock_sensitive.return_value = (0, None)

        with patch('app.services.risk_service._image_score', new_callable=AsyncMock) as mock_image:
            mock_image.return_value = (85, "违规图片")

            result = await evaluate_content(
                db_session,
                "正常文本",
                images=["https://example.com/bad.jpg"]
            )

            assert result.action == "reject"
            assert result.score == 85

    @pytest.mark.asyncio
    async def test_combined_risks(self, db_session: AsyncSession):
        """测试多种风险组合"""
        with patch('app.services.risk_service._text_sensitive_score_from_db', new_callable=AsyncMock) as mock_sensitive:
            mock_sensitive.return_value = (70, "敏感词")

        with patch('app.services.risk_service._image_score', new_callable=AsyncMock) as mock_image:
            mock_image.return_value = (60, "可疑图片")

            result = await evaluate_content(
                db_session,
                "包含敏感词 联系我13812345678",
                images=["https://example.com/img.jpg"]
            )

            # 应该取最高分
            assert result.score >= 70
            assert "敏感词" in result.reason or "含联系方式" in result.reason

    @pytest.mark.asyncio
    async def test_empty_content(self, db_session: AsyncSession):
        """测试空内容"""
        result = await evaluate_content(db_session, "")

        assert result.action == "approve"
        assert result.score == 0

    @pytest.mark.asyncio
    async def test_max_score_80_reject(self, db_session: AsyncSession):
        """测试80分触发拒绝"""
        with patch('app.services.risk_service._text_sensitive_score_from_db', new_callable=AsyncMock) as mock_sensitive:
            mock_sensitive.return_value = (80, "高风险")

            result = await evaluate_content(db_session, "高风险内容")

            assert result.action == "reject"

    @pytest.mark.asyncio
    async def test_score_50_manual(self, db_session: AsyncSession):
        """测试50分触发人工审核"""
        with patch('app.services.risk_service._text_sensitive_score_from_db', new_callable=AsyncMock) as mock_sensitive:
            mock_sensitive.return_value = (50, "中风险")

            result = await evaluate_content(db_session, "中风险内容")

            assert result.action == "manual"

    @pytest.mark.asyncio
    async def test_score_below_50_approve(self, db_session: AsyncSession):
        """测试低于50分通过"""
        with patch('app.services.risk_service._text_sensitive_score_from_db', new_callable=AsyncMock) as mock_sensitive:
            mock_sensitive.return_value = (49, "低风险")

            result = await evaluate_content(db_session, "低风险内容")

            assert result.action == "approve"
