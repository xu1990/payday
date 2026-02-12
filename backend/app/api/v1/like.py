"""
点赞 - 帖子/评论点赞与取消；PRD：POST=点赞，DELETE=取消
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.like import LikeResponse
from app.services import like_service

router = APIRouter(tags=["likes"])


@router.post("/posts/{post_id}/like", response_model=LikeResponse)
async def like_post(
    post_id: str,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """对帖子点赞；已赞则幂等返回 200 + 已有 like，新赞返回 201。"""
    r = await db.execute(select(Post).where(Post.id == post_id))
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    like, created = await like_service.like_post(db, current_user.id, post_id)
    response.status_code = 201 if created else 200
    return LikeResponse.model_validate(like)


@router.delete("/posts/{post_id}/like", status_code=204)
async def unlike_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消帖子点赞。"""
    ok = await like_service.unlike_post(db, current_user.id, post_id)
    if not ok:
        raise HTTPException(status_code=404, detail="未点赞或帖子不存在")
    return None


@router.post("/comments/{comment_id}/like", response_model=LikeResponse)
async def like_comment(
    comment_id: str,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """对评论点赞；已赞则幂等返回 200 + 已有 like，新赞返回 201。"""
    r = await db.execute(select(Comment).where(Comment.id == comment_id))
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    like, created = await like_service.like_comment(db, current_user.id, comment_id)
    response.status_code = 201 if created else 200
    return LikeResponse.model_validate(like)


@router.delete("/comments/{comment_id}/like", status_code=204)
async def unlike_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消评论点赞。"""
    ok = await like_service.unlike_comment(db, current_user.id, comment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="未点赞或评论不存在")
    return None
