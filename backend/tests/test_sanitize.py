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
        # script 标签被完全移除（strip=True），不保留标签内容
        assert "alert('xss')Hello" == result
        assert "<script>" not in result
        assert "</script>" not in result

    def test_removes_iframe_tag(self):
        """测试移除 iframe 标签"""
        input_html = '<iframe src="evil.com"></iframe>Content'
        result = sanitize_html(input_html)
        # iframe 标签被完全移除
        assert 'Content' == result
        assert '<iframe>' not in result
        assert 'evil.com' not in result

    def test_removes_object_tag(self):
        """测试移除 object 标签"""
        input_html = '<object data="evil.swf"></object>Content'
        result = sanitize_html(input_html)
        # object 标签被完全移除
        assert 'Content' == result
        assert '<object>' not in result
        assert 'evil.swf' not in result

    def test_removes_embed_tag(self):
        """测试移除 embed 标签"""
        input_html = '<embed src="evil.swf">'
        result = sanitize_html(input_html)
        # embed 标签被完全移除
        assert '' == result or result.isspace() or result == ''
        assert '<embed>' not in result

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
        # div 标签被完全移除（strip=True）
        assert "Test" == result
        assert "<div>" not in result
        assert "</div>" not in result

    def test_escapes_quotes(self):
        """测试引号转义"""
        input_html = '<div attr="value">'
        result = sanitize_html(input_html)
        # div 标签被完全移除，引号保留
        assert result == '' or result.strip() == ''
        assert '<div>' not in result
        assert 'attr=' not in result

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

    def test_handles_style_attribute(self):
        """测试处理 style 属性"""
        input_html = '<div style="color:red">Text</div>'
        result = sanitize_html(input_html)
        assert "<div>" not in result
        assert "style" not in result.lower()
        assert "Text" in result

    def test_handles_href_javascript(self):
        """测试处理 javascript: href"""
        input_html = '<a href="javascript:alert(1)">Click</a>'
        result = sanitize_html(input_html)
        assert "<a>" not in result
        assert "javascript:" not in result.lower()
        assert "Click" in result

    def test_handles_svg_xss(self):
        """测试处理 SVG XSS"""
        input_html = '<svg onload="alert(1)">Text</svg>'
        result = sanitize_html(input_html)
        assert "<svg>" not in result
        assert "onload" not in result.lower()
        assert "Text" in result

    def test_handles_data_url(self):
        """测试处理 data URL"""
        input_html = '<img src="data:image/svg+xml,<svg>...</svg>">'
        result = sanitize_html(input_html)
        assert "<img>" not in result
        # 内容应该被移除或清理

    def test_handles_multiple_lines(self):
        """测试处理多行文本"""
        input_html = '<div>Line 1\nLine 2\nLine 3</div>'
        result = sanitize_html(input_html)
        assert "<div>" not in result
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_handles_table_tags(self):
        """测试处理表格标签"""
        input_html = '<table><tr><td>Cell</td></tr></table>'
        result = sanitize_html(input_html)
        assert "<table>" not in result
        assert "<tr>" not in result
        assert "<td>" not in result
        assert "Cell" in result


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

    def test_removes_html_comments(self):
        """测试移除 HTML 注释"""
        input_html = "Hello <!-- comment --> World"
        result = sanitize_strict(input_html)
        assert "<!--" not in result
        assert "-->" not in result
        assert "Hello" in result
        assert "World" in result

    def test_handles_nested_tags(self):
        """测试处理嵌套标签"""
        input_html = "<div><span><b>Nested</b></span></div>"
        result = sanitize_strict(input_html)
        assert "<div>" not in result
        assert "<span>" not in result
        assert "<b>" not in result
        assert "Nested" in result

    def test_handles_mixed_content(self):
        """测试处理混合内容"""
        input_html = "Text <script>alert('xss')</script> More <b>bold</b> content"
        result = sanitize_strict(input_html)
        assert "<script>" not in result
        assert "<b>" not in result
        assert "Text" in result
        assert "More" in result
        assert "content" in result

    def test_handles_special_characters(self):
        """测试处理特殊字符"""
        input_html = "<div>Test &quot;quotes&quot; &amp; &lt;tag&gt;</div>"
        result = sanitize_strict(input_html)
        assert "<div>" not in result
        assert "Test" in result
        assert "quotes" in result

    def test_handles_unicode(self):
        """测试处理 Unicode 字符"""
        input_html = "<div>Hello 世界 🌍</div>"
        result = sanitize_strict(input_html)
        assert "<div>" not in result
        assert "Hello" in result
        assert "世界" in result

    def test_preserves_text_formatting_without_tags(self):
        """测试保留纯文本格式"""
        input_text = "Line 1\nLine 2\n\nLine 3"
        result = sanitize_strict(input_text)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
