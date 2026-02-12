"""
缓存相关的 Pydantic schemas
"""
from pydantic import BaseModel


class PreheatResponse(BaseModel):
    """缓存预热响应"""

    success: bool
    message: str
    details: dict[str, int] = {}
