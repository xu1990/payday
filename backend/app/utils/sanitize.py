"""
内容净化工具 - 防止 XSS 攻击
"""
import re
import html
from typing import Optional


def sanitize_html(content: Optional[str]) -> Optional[str]:
    """
    净化用户输入的文本内容，防止 XSS 攻击

    策略：
    1. 转义 HTML 特殊字符
    2. 移除危险的 HTML 标签（如果存在）
    3. 移除危险的 JavaScript 代码模式

    注意：这是一个基础实现，生产环境建议使用 bleach 库：
    pip install bleach
    import bleach
    return bleach.clean(content, tags=[], strip=True)
    """
    if not content:
        return content

    # 移除已知的危险标签和属性
    # 移除 script 标签
    content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', content, flags=re.IGNORECASE)
    # 移除 iframe 标签
    content = re.sub(r'<iframe\b[^<]*>.*?</iframe>', '', content, flags=re.IGNORECASE | re.DOTALL)
    # 移除 object 标签
    content = re.sub(r'<object\b[^<]*>.*?</object>', '', content, flags=re.IGNORECASE | re.DOTALL)
    # 移除 embed 标签
    content = re.sub(r'<embed\b[^<]*>', '', content, flags=re.IGNORECASE)
    # 移除 on* 事件处理器（如 onclick, onload）
    content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)

    # HTML 转义（确保特殊字符被正确转义）
    # 使用 html.escape 将 <, >, &, ", ' 转义为 HTML 实体
    content = html.escape(content)

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

    # 移除所有 HTML 标签
    content = re.sub(r'<[^>]+>', '', content)

    # HTML 实体解码（处理 &lt; 等）
    content = html.unescape(content)

    # 再次转义，确保安全
    content = html.escape(content)

    # 截断到最大长度
    if len(content) > max_length:
        content = content[:max_length]

    return content
