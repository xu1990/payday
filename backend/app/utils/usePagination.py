"""
分页工具类 - 统一分页逻辑，避免代码重复
提供计算分页参数的通用方法
"""
from typing import Generic, Tuple, List, Optional
from sqlalchemy import func, select

def calculate_pagination(limit: int, offset: int) -> Tuple[int, int]:
    """
    计算分页参数

    Args:
        limit: 每页数量
        offset: 偏移量

    Returns:
        (page, page_size): 页码和每页数量
    """
    page_size = limit
    page = (offset // limit) + 1 if limit > 0 else 1
    return page, page_size


def apply_pagination(query, page: int, page_size: int) -> List:
    """
    应用分页到查询

    Args:
        query: SQLAlchemy查询对象
        page: 页码（从1开始）
        page_size: 每页数量

    Returns:
        分页后的列表
    """
    offset = (page - 1) * page_size
    return query.limit(page_size).offset(offset)


def paginated_response(
    items: List,
    total: int,
    page: int,
    page_size: int
) -> dict:
    """
    构建分页响应字典

    Args:
        items: 数据列表
        total: 总数
        page: 当前页码
        page_size: 每页数量

    Returns:
        分页响应字典
    """
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        }
