"""
内容净化工具 - 防止 XSS 攻击

使用 bleach 库进行白名单式净化，避免 ReDoS 攻击
"""
from typing import Optional

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    import re
    import html


def sanitize_html(content: Optional[str]) -> Optional[str]:
    """
    净化用户输入的文本内容，防止 XSS 攻击

    SECURITY: 使用 bleach 库的白名单式净化，避免 ReDoS 攻击
    - 不允许任何 HTML 标签
    - 移除所有危险内容
    - 使用经过实战检验的库

    如果 bleach 不可用，则回退到基础实现（次优方案）
    """
    if not content:
        return content

    if BLEACH_AVAILABLE:
        # 使用 bleach 的白名单式净化（最安全）
        return bleach.clean(
            content,
            tags=[],           # 不允许任何 HTML 标签
            strip=True,         # 移除而非转义标签
            strip_comments=True  # 移除 HTML 注释
        )
    else:
        # 回退方案：基础 HTML 转义
        # WARNING: 不如 bleach 安全，但在 bleach 不可用时提供基本保护
        content = html.escape(content, quote=False)
        # 移除控制字符（除了换行、制表符、回车）
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\t\r')
        return content


def sanitize_strict(content: Optional[str], max_length: int = 5000) -> Optional[str]:
    """
    严格模式净化：移除所有 HTML 标签，只保留纯文本

    适用于：
    - 用户昵称
    - 简短评论
    - 不需要 HTML 格式的场景
    """
    if not content:
        return content

    if BLEACH_AVAILABLE:
        # 使用 bleach 进行彻底净化
        cleaned = bleach.clean(
            content,
            tags=[],
            strip=True,
            strip_comments=True
        )
    else:
        # 回退方案：移除 HTML 标签并转义
        cleaned = html.unescape(re.sub(r'<[^>]*>', '', content))
        cleaned = html.escape(cleaned)

    # 截断到最大长度
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned
