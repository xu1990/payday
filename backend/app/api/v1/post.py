"""
帖子 - 发帖、列表（热门/最新）、详情
"""
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.post import PostCreate, PostResponse
from app.services.post_service import create as create_post, get_by_id, list_posts
from app.tasks.risk_check import run_risk_check_for_post

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostResponse)
async def post_create(
    body: PostCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 发帖使用当前用户匿名昵称（与 PRD/技术方案一致）
    post = await create_post(db, current_user.id, body, anonymous_name=current_user.anonymous_name)
    background_tasks.add_task(run_risk_check_for_post, post.id)
    return PostResponse.model_validate(post)


@router.get("", response_model=list[PostResponse])
async def post_list(
    sort: Literal["hot", "latest"] = Query("latest", description="hot=热门 latest=最新"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    posts = await list_posts(db, sort=sort, limit=limit, offset=offset)
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/{post_id}", response_model=PostResponse)
async def post_get(
    post_id: str,
    db: AsyncSession = Depends(get_db),
):
    post = await get_by_id(db, post_id, only_approved=True)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在或未通过")
    return PostResponse.model_validate(post)
