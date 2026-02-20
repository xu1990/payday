"""
点赞 - 帖子/评论点赞与取消；PRD：POST=点赞，DELETE=取消
"""
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import success_response, NotFoundException
from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.schemas.like import LikeResponse
from app.services import like_service

router = APIRouter(tags=["likes"])


@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: str,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """对帖子点赞；已赞则幂等返回 200 + 已有 like，新赞返回 201。"""
    r = await db.execute(select(Post).where(Post.id == post_id))
    if r.scalar_one_or_none() is None:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("资源不存在")
    like, created = await like_service.like_post(db, current_user.id, post_id)
    response.status_code = 201 if created else 200
    return success_response(data=LikeResponse.model_validate(like).model_dump(mode='json'), message="点赞成功")


@router.delete("/posts/{post_id}/like", status_code=204)
async def unlike_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消帖子点赞。"""
    ok = await like_service.unlike_post(db, current_user.id, post_id)
    if not ok:
        raise NotFoundException("资源不存在")
    return None


@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: str,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """对评论点赞；已赞则幂等返回 200 + 已有 like，新赞返回 201。"""
    r = await db.execute(select(Comment).where(Comment.id == comment_id))
    if r.scalar_one_or_none() is None:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("资源不存在")
    like, created = await like_service.like_comment(db, current_user.id, comment_id)
    response.status_code = 201 if created else 200
    return success_response(data=LikeResponse.model_validate(like).model_dump(mode='json'), message="点赞成功")


@router.delete("/comments/{comment_id}/like", status_code=204)
async def unlike_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消评论点赞。"""
    ok = await like_service.unlike_comment(db, current_user.id, comment_id)
    if not ok:
        raise NotFoundException("资源不存在")
    return None


@router.get("/me/likes")
async def get_my_likes(
    target_type: Literal["post", "comment"] = Query("post", description="点赞目标类型：post 或 comment"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取我的点赞列表

    返回当前用户点赞过的帖子或评论列表
    """
    from sqlalchemy import func
    from app.schemas.post import PostResponse

    if target_type == "post":
        # 获取总数
        count_result = await db.execute(
            select(func.count(Like.id))
            .where(
                Like.user_id == current_user.id,
                Like.target_type == "post"
            )
        )
        total = count_result.scalar_one()

        # 查询用户点赞的帖子ID列表（按点赞时间倒序）
        result = await db.execute(
            select(Like.target_id)
            .where(
                Like.user_id == current_user.id,
                Like.target_type == "post"
            )
            .order_by(Like.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        target_ids = [row[0] for row in result.all()]

        if not target_ids:
            return success_response(data={"items": [], "total": total})

        # 查询帖子详情
        posts_result = await db.execute(
            select(Post)
            .where(
                Post.id.in_(target_ids),
                Post.status == "normal",
                Post.risk_status == "approved"
            )
        )
        posts = posts_result.scalars().all()

        # 按 target_ids 顺序排序
        posts_dict = {post.id: post for post in posts}
        sorted_posts = [posts_dict[tid] for tid in target_ids if tid in posts_dict]

        # 填充 is_liked 字段（用户自己的点赞列表，所有都是已点赞）
        items = []
        for post in sorted_posts:
            post.is_liked = True
            # 使用 Pydantic 序列化
            items.append(PostResponse.model_validate(post).model_dump(mode='json'))

        return success_response(data={"items": items, "total": total})

    else:  # comment
        # 获取总数
        count_result = await db.execute(
            select(func.count(Like.id))
            .where(
                Like.user_id == current_user.id,
                Like.target_type == "comment"
            )
        )
        total = count_result.scalar_one()

        # 查询用户点赞的评论ID列表
        result = await db.execute(
            select(Like.target_id)
            .where(
                Like.user_id == current_user.id,
                Like.target_type == "comment"
            )
            .order_by(Like.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        target_ids = [row[0] for row in result.all()]

        if not target_ids:
            return success_response(data={"items": [], "total": total})

        # 查询评论详情
        from app.models.comment import Comment
        comments_result = await db.execute(
            select(Comment)
            .where(Comment.id.in_(target_ids))
        )
        comments = comments_result.scalars().all()

        # 按 target_ids 顺序排序
        comments_dict = {comment.id: comment for comment in comments}
        sorted_comments = [comments_dict[tid] for tid in target_ids if tid in comments_dict]

        # 转换为字典格式
        items = []
        for comment in sorted_comments:
            items.append({
                "id": comment.id,
                "post_id": comment.post_id,
                "user_id": comment.user_id,
                "content": comment.content,
                "like_count": comment.like_count or 0,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
            })

        return success_response(data={"items": items, "total": total})
