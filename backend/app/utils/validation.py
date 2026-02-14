"""
输入验证工具 - 防止无效数据进入系统
"""
import re
from uuid import UUID
from typing import Optional

from app.core.exceptions import ValidationException


def validate_uuid(uuid_str: str, field_name: str = "ID") -> UUID:
    """
    验证UUID格式

    Args:
        uuid_str: 待验证的UUID字符串
        field_name: 字段名称（用于错误消息）

    Returns:
        验证后的UUID对象

    Raises:
        ValidationException: UUID格式无效时
    """
    try:
        return UUID(uuid_str)
    except ValueError:
        raise ValidationException(
            message=f"无效的{field_name}格式",
            details={"field": field_name, "value": uuid_str},
        )


def is_valid_uuid(uuid_str: str) -> bool:
    """
    快速检查UUID格式是否有效（不抛出异常）

    Args:
        uuid_str: 待检查的UUID字符串

    Returns:
        是否为有效的UUID
    """
    try:
        UUID(uuid_str)
        return True
    except ValueError:
        return False


def validate_anonymous_name(name: str) -> None:
    """
    验证用户匿名昵称

    规则：
    - 长度：1-50字符
    - 仅允许：中文、字母、数字、空格、连字符、下划线
    - 不允许：特殊字符、表情符号

    Args:
        name: 待验证的昵称

    Raises:
        ValidationException: 昵称格式无效时
    """
    if not name or len(name) > 50:
        raise ValidationException(
            message="匿名昵称长度必须在1-50字符之间",
            details={"field": "anonymous_name", "length": len(name) if name else 0},
        )

    # 使用正则表达式验证昵称格式
    # 允许：中文(\u4e00-\u9fff)、字母、数字、空格、连字符、下划线
    if not re.match(r'^[\w\u4e00-\u9fff\s\-_]+$', name):
        raise ValidationException(
            message="匿名昵称只能包含中文、字母、数字、空格、连字符和下划线",
            details={"field": "anonymous_name", "value": name},
        )


def validate_salary_amount(amount: float) -> None:
    """
    验证工资金额

    Args:
        amount: 待验证的金额

    Raises:
        ValidationException: 金额无效时
    """
    if amount < 0:
        raise ValidationException(
            message="工资金额不能为负数",
            details={"field": "amount", "value": amount},
        )

    # 检查金额是否在合理范围内（0.01 - 999999.99）
    if amount < 0.01 or amount > 999999.99:
        raise ValidationException(
            message="工资金额超出允许范围（0.01-999999.99）",
            details={"field": "amount", "value": amount},
        )


def validate_content_length(content: str, max_length: int = 10000) -> None:
    """
    验证内容长度

    Args:
        content: 待验证的内容
        max_length: 最大允许长度

    Raises:
        ValidationException: 内容长度超出限制时
    """
    if len(content) > max_length:
        raise ValidationException(
            message=f"内容长度不能超过{max_length}字符",
            details={
                "field": "content",
                "length": len(content),
                "max_length": max_length,
            },
        )


def sanitize_user_input(text: str) -> str:
    """
    基础的用户输入清理（移除危险字符）

    注意：这不替代完整的HTML转义，仅作为额外防护层
    使用 app.utils.sanitize 进行完整的HTML清理

    Args:
        text: 待清理的文本

    Returns:
        清理后的文本
    """
    # 移除控制字符（除了换行、制表符、回车）
    cleaned = ''.join(
        char for char in text
        if ord(char) >= 32 or char in '\n\t\r'
    )
    return cleaned
