"""
帖子 - 发帖、列表（热门/最新）、详情
"""
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, AuthenticationException, BusinessException, success_response
from app.core.deps import get_current_user, get_current_user_optional, rate_limit_post
from app.models.user import User
from app.schemas.post import PostCreate, PostResponse
from app.services.post_service import create as create_post, get_by_id, list_posts, search_posts
from app.tasks.risk_check import run_risk_check_for_post

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/search")
async def post_search(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    tags: Optional[str] = Query(None, description="标签搜索，逗号分隔"),
    user_id: Optional[str] = Query(None, description="用户ID筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    city: Optional[str] = Query(None, description="城市筛选"),
    salary_range: Optional[str] = Query(None, description="工资区间筛选"),
    sort: Literal["hot", "latest"] = Query("latest", description="hot=热门 latest=最新"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """搜索帖子"""
    posts, total = await search_posts(
        db,
        keyword=keyword,
        tags=tags.split(",") if tags else None,
        user_id=user_id,
        industry=industry,
        city=city,
        salary_range=salary_range,
        sort=sort,
        limit=limit,
        offset=offset
    )
    items = [PostResponse.model_validate(p) for p in posts]
    return success_response(data={"items": items, "total": total}, message="搜索成功")


@router.post("")
async def post_create(
    body: PostCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(rate_limit_post),
    db: AsyncSession = Depends(get_db),
):
    # 发帖使用当前用户匿名昵称（与 PRD/技术方案一致）
    # SECURITY: 速率限制已通过 _rate_limit 依赖应用
    post = await create_post(db, current_user.id, body, anonymous_name=current_user.anonymous_name)
    background_tasks.add_task(run_risk_check_for_post, post.id)
    return success_response(data=PostResponse.model_validate(post).model_dump(mode='json'), message="发帖成功")


@router.get("")
async def post_list(
    sort: Literal["hot", "latest"] = Query("latest", description="hot=热门 latest=最新"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    posts = await list_posts(
        db,
        sort=sort,
        limit=limit,
        offset=offset,
        current_user_id=current_user.id if current_user else None
    )
    data = [PostResponse.model_validate(p).model_dump(mode='json') for p in posts]
    return success_response(data=data, message="获取帖子列表成功")


@router.get("/{post_id}")
async def post_get(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    # 获取帖子详情并增加浏览量（从缓存计数）
    post = await get_by_id(
        db,
        post_id,
        only_approved=True,
        increment_view=True,
        current_user_id=current_user.id if current_user else None
    )
    if not post:
        raise NotFoundException("资源不存在")
    return success_response(data=PostResponse.model_validate(post).model_dump(mode='json'), message="获取帖子详情成功")
