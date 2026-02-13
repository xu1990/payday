"""
话题 Pydantic Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class TopicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="话题名称")
    description: Optional[str] = Field(None, max_length=500, description="话题描述")
    cover_image: Optional[str] = Field(None, max_length=500, description="封面图片URL")
    sort_order: int = Field(0, ge=0, description="排序权重")


class TopicUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class TopicResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    cover_image: Optional[str]
    post_count: int
    is_active: bool
    sort_order: int
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class TopicListResponse(BaseModel):
    items: list[TopicResponse]
    total: int
