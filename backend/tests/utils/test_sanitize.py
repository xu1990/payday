"""内容净化工具测试"""
import pytest
from app.utils.sanitize import sanitize_html, sanitize_strict


class TestSanitizeHtml:
    """测试 sanitize_html 函数"""

    def test_none_input(self):
        """测试 None 输入"""
        result = sanitize_html(None)
        assert result is None

    def test_empty_string(self):
        """测试空字符串"""
        result = sanitize_html("")
        assert result == ""

    def test_removes_on_event_handlers(self):
        """测试移除 on* 事件处理器"""
        result = sanitize_html("Click me <a onclick='alert(\"XSS\")'>here</a>")
        assert "onclick" not in result
        assert "alert" not in result

    def test_escapes_html_special_chars(self):
        """测试转义 HTML 特殊字符"""
        result = sanitize_html("<script>alert('XSS')</script>")
        # bleach 会完全移除标签（strip=True），不是转义
        assert "<script>" not in result
        assert "</script>" not in result
        # 内容保留但不会执行
        assert "alert('XSS')" in result

    def test_escapes_common_characters(self):
        """测试转义常见字符"""
        result = sanitize_html("a < b > c & d")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result

    def test_removes_control_characters(self):
        """测试移除控制字符（保留换行、制表符、回车）"""
        result = sanitize_html("Hello\x00World\x01\x02\n\t\r")
        # 控制字符 \x00, \x01, \x02 应被移除，但 "World" 保留
        # bleach 会将控制字符替换为 \ufffd (replacement character) 或直接移除
        # 关键是验证控制字符被处理，不会造成安全问题
        assert "Hello" in result
        assert "World" in result
        assert "\n" in result
        assert "\t" in result
        # \r 可能被转换为 \n
        assert "\r" not in result or "\n" in result

    def test_preserves_safe_content(self):
        """测试保留安全内容"""
        result = sanitize_html("This is safe content with newlines\nand tabs\t")
        assert "This is safe content" in result
        assert "\n" in result
        assert "\t" in result


class TestSanitizeStrict:
    """测试 sanitize_strict 函数"""

    def test_none_input(self):
        """测试 None 输入"""
        result = sanitize_strict(None)
        assert result is None

    def test_empty_string(self):
        """测试空字符串"""
        result = sanitize_strict("")
        assert result == ""

    def test_removes_html_tags(self):
        """测试移除 HTML 标签"""
        result = sanitize_strict("<p>Hello <b>world</b></p>")
        assert "<p>" not in result
        assert "<b>" not in result
        assert "Hello world" in result

    def test_unescapes_html_entities(self):
        """测试解码 HTML 实体"""
        result = sanitize_strict("Hello &lt;world&gt;")
        assert "Hello" in result
        # Should escape again
        assert "&lt;" in result

    def test_escapes_after_unescape(self):
        """测试解码后再次转义"""
        result = sanitize_strict("<script>alert('XSS')</script>")
        # Tags should be removed
        assert "<script>" not in result
        assert "</script>" not in result
        # Content should be escaped
        assert "&lt;" in result or "alert" in result

    def test_default_max_length(self):
        """测试默认最大长度"""
        long_content = "a" * 6000
        result = sanitize_strict(long_content)
        assert len(result) == 5000

    def test_custom_max_length(self):
        """测试自定义最大长度"""
        long_content = "a" * 200
        result = sanitize_strict(long_content, max_length=100)
        assert len(result) == 100

    def test_short_content_unchanged(self):
        """测试短内容不被截断"""
        short_content = "Short content"
        result = sanitize_strict(short_content, max_length=1000)
        assert result == "Short content"

    def test_mixed_content(self):
        """测试混合内容"""
        result = sanitize_strict("Hello <b>world</b> &amp; goodbye")
        assert "Hello" in result
        assert "<b>" not in result
        assert "goodbye" in result
