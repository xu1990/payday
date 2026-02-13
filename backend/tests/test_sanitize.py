"""
内容净化工具测试
"""
import pytest
from app.utils.sanitize import sanitize_html, sanitize_strict


class TestSanitizeHtml:
    """测试 HTML 净化功能"""

    def test_removes_script_tag(self):
        """测试移除 script 标签"""
        input_html = "<script>alert('xss')</script>Hello"
        result = sanitize_html(input_html)
        # script 标签被移除，其他内容被转义
        assert "&lt;script&gt;alert('xss')&lt;/script&gt;Hello" == result

    def test_removes_iframe_tag(self):
        """测试移除 iframe 标签"""
        input_html = '<iframe src="evil.com"></iframe>Content'
        result = sanitize_html(input_html)
        assert "&lt;iframe src=\"evil.com\"&gt;&lt;/iframe&gt;Content" == result

    def test_removes_object_tag(self):
        """测试移除 object 标签"""
        input_html = '<object data="evil.swf"></object>Content'
        result = sanitize_html(input_html)
        assert "&lt;object data=\"evil.swf\"&gt;&lt;/object&gt;Content" == result

    def test_removes_embed_tag(self):
        """测试移除 embed 标签"""
        input_html = '<embed src="evil.swf">'
        result = sanitize_html(input_html)
        assert "&lt;embed src=\"evil.swf\"&gt;" == result

    def test_removes_event_handlers(self):
        """测试移除 on* 事件处理器"""
        input_html = '<div onclick="evil()">Click</div>'
        result = sanitize_html(input_html)
        # onclick 应该被移除
        assert "onclick" not in result.lower()

    def test_escapes_html_entities(self):
        """测试 HTML 实体转义"""
        input_html = "<div>Test</div>"
        result = sanitize_html(input_html)
        assert "&lt;div&gt;Test&lt;/div&gt;" == result

    def test_escapes_quotes(self):
        """测试引号转义"""
        input_html = '<div attr="value">'
        result = sanitize_html(input_html)
        # 引号不被转义（quote=False），但 < > 被转义
        assert "&lt;" in result and "&gt;" in result
        assert result == '&lt;div attr="value"&gt;'

    def test_escapes_ampersand(self):
        """测试 & 符号转义"""
        input_html = "Tom & Jerry"
        result = sanitize_html(input_html)
        assert "&amp;" in result

    def test_removes_control_characters(self):
        """测试移除控制字符"""
        input_html = "Hello\x00World\x1F"
        result = sanitize_html(input_html)
        # 控制字符应该被移除
        assert "\x00" not in result
        assert "\x1F" not in result

    def test_preserves_newlines_and_tabs(self):
        """测试保留换行符和制表符"""
        input_html = "Line 1\nLine 2\tTabbed"
        result = sanitize_html(input_html)
        assert "\n" in result or "&#10;" in result or "<br>" in result
        assert "\t" in result or "&#9;" in result or "	" in result

    def test_handles_empty_input(self):
        """测试空输入"""
        assert sanitize_html(None) is None
        assert sanitize_html("") == ""

    def test_handles_complex_xss(self):
        """测试复杂 XSS 攻击"""
        input_html = '<img src=x onerror="alert(1)">'
        result = sanitize_html(input_html)
        # onerror 应该被移除
        assert "onerror" not in result.lower()


class TestSanitizeStrict:
    """测试严格模式净化功能"""

    def test_removes_all_html_tags(self):
        """测试移除所有 HTML 标签"""
        input_html = "<div><span>Bold</span></div>"
        result = sanitize_strict(input_html)
        assert "<div>" not in result
        assert "<span>" not in result
        assert "Bold" in result

    def test_truncates_long_content(self):
        """测试截断过长内容"""
        input_html = "a" * 10000
        result = sanitize_strict(input_html, max_length=100)
        assert len(result) <= 100

    def test_defaults_max_length(self):
        """测试默认最大长度"""
        long_input = "a" * 10000
        result = sanitize_strict(long_input)
        # 默认 max_length=5000
        assert len(result) <= 5000

    def test_handles_plain_text(self):
        """测试纯文本输入"""
        input_text = "Just plain text"
        result = sanitize_strict(input_text)
        # 纯文本保留，但被 HTML 转义
        assert "Just plain text" in result or "Just plain text" == result

    def test_handles_empty_input(self):
        """测试空输入"""
        assert sanitize_strict(None) is None
        assert sanitize_strict("") == ""
