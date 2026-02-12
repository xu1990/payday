"""
内容推荐接口 - 热门帖子、个性化推荐、话题推荐
"""
from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.post import PostResponse
from app.services import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/hot", response_model=list[PostResponse])
async def get_hot_posts(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db),
):
    """热门帖子推荐（基于点赞、评论、浏览热度）。"""
    posts = await recommendation_service.recommend_posts_hot(db, limit)
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/feed", response_model=list[PostResponse])
async def get_personalized_feed(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """个性化推荐（基于关注用户的协同过滤）。"""
    posts = await recommendation_service.recommend_posts_for_user(
        db, current_user.id, limit
    )
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/topics")
async def get_recommended_topics(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db),
):
    """推荐话题（按帖子数和活跃度）。"""
    topics = await recommendation_service.recommend_topics(db, limit)
    return {"items": topics}
