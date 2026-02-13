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
    1. 移除 on* 事件处理器（如 onclick, onload）
    2. 转义 HTML 特殊字符（<, >, &）
    3. 移除控制字符（除了换行、制表符、回车）

    注意：这是一个基础实现，生产环境建议使用 bleach 库：
    pip install bleach
    import bleach
    return bleach.clean(content, tags=[], strip=True)
    """
    if not content:
        return content

    # 移除 on* 事件处理器（如 onclick, onload）- 在转义前处理
    content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)

    # HTML 转义（确保特殊字符被正确转义）
    # 使用 html.escape 将 <, >, & 转义为 HTML 实体
    # quote=False 表示不转义引号，因为引号在文本内容中通常是安全的
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
