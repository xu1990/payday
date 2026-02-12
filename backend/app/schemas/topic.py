"""
话题 Pydantic Schemas
"""
from pydantic import BaseModel, Field


class TopicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="话题名称")
    description: str | None = Field(None, max_length=500, description="话题描述")
    cover_image: str | None = Field(None, max_length=500, description="封面图片URL")
    sort_order: int = Field(0, ge=0, description="排序权重")


class TopicUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = Field(None, max_length=500)
    cover_image: str | None = Field(None, max_length=500)
    is_active: bool | None = None
    sort_order: int | None = Field(None, ge=0)


class TopicResponse(BaseModel):
    id: str
    name: str
    description: str | None
    cover_image: str | None
    post_count: int
    is_active: bool
    sort_order: int
    created_at: str
    updated_at: str | None

    class Config:
        from_attributes = True


class TopicListResponse(BaseModel):
    items: list[TopicResponse]
    total: int
