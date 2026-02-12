"""
服务层测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.risk_service import (
    RiskResult,
    evaluate_content,
    _text_contact_score,
    _text_sensitive_score,
)


class TestTextContactScore:
    """测试联系方式检测"""

    def test_no_contact(self):
        """测试无联系方式"""
        score, reason = _text_contact_score("这是一条正常的文本内容")
        assert score == 0
        assert reason is None

    def test_phone_number(self):
        """测试手机号检测"""
        score, reason = _text_contact_score("我的手机号是13812345678")
        assert score == 80
        assert "联系方式" in reason

    def test_email(self):
        """测试邮箱检测"""
        score, reason = _text_contact_score("联系我 test@example.com")
        assert score == 80
        assert "联系方式" in reason

    def test_qq(self):
        """测试QQ号检测"""
        score, reason = _text_contact_score("QQ号：123456789")
        assert score == 80
        assert "联系方式" in reason

    def test_wechat(self):
        """测试微信号检测"""
        score, reason = _text_contact_score("我的微信 abc123456")
        assert score == 80
        assert "联系方式" in reason


class TestTextSensitiveScore:
    """测试敏感词检测"""

    def test_no_sensitive_words(self):
        """测试无敏感词"""
        score, reason = _text_sensitive_score("这是正常内容")
        assert score == 0
        assert reason is None

    def test_sensitive_word_found(self):
        """测试敏感词命中"""
        score, reason = _text_sensitive_score("这是违禁词1的内容")
        assert score == 90
        assert "违规内容" in reason

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        score, reason = _text_sensitive_score("这是违禁词1的内容")
        assert score == 90
        assert "违规内容" in reason


class TestEvaluateContent:
    """测试综合内容评估"""

    @pytest.mark.asyncio
    async def test_safe_content(self):
        """测试安全内容"""
        result = await evaluate_content(
            content="这是一条正常的帖子内容",
            images=None,
            use_yu=False,  # 不使用天御服务
        )
        assert result.score < 50
        assert result.action == "approve"

    @pytest.mark.asyncio
    async def test_contact_info_content(self):
        """测试含联系方式内容"""
        result = await evaluate_content(
            content="联系我 13812345678",
            images=None,
            use_yu=False,
        )
        assert result.score >= 80
        assert result.action == "reject"
        assert "联系方式" in result.reason

    @pytest.mark.asyncio
    async def test_manual_review_content(self):
        """测试需要人工审核的内容"""
        # 创建一个中等风险的场景
        with patch('app.services.risk_service._text_yu_score', return_value=(50, "需要人工审核")):
            result = await evaluate_content(
                content="待审核内容",
                images=None,
                use_yu=True,
            )
            assert result.score >= 50
            assert result.action == "manual"
