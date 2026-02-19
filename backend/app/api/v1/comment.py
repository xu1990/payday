"""
评论 - 帖子下评论列表、发表评论/回复、删除；与技术方案 2.1.1 一致
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, AuthenticationException, BusinessException, success_response
from app.core.deps import get_current_user
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.comment_service import (
    create as create_comment,
    delete as delete_comment,
    get_by_id as get_comment,
    list_roots_with_replies,
)
from app.tasks.risk_check import run_risk_check_for_comment

router = APIRouter(prefix="/posts", tags=["comments"])


@router.get("/{post_id}/comments")
async def comment_list(
    post_id: str,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """帖子下的评论列表（根评论分页，带二级回复）。"""
    roots = await list_roots_with_replies(db, post_id, limit=limit, offset=offset)
    data = [CommentResponse.model_validate(r).model_dump() for r in roots]
    return success_response(data=data, message="获取评论列表成功")


@router.post("/{post_id}/comments")
async def comment_create(
    post_id: str,
    body: CommentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发表评论或回复：不传 parent_id 为根评论，传 parent_id 为回复。"""
    r = await db.execute(select(Post).where(Post.id == post_id))
    post = r.scalar_one_or_none()
    if not post or post.status != "normal" or post.risk_status != "approved":
        raise NotFoundException("资源不存在")

    # SECURITY: 检查用户是否被帖子作者拉黑
    # TODO: 实现用户拉黑/屏蔽功能后，需要添加以下检查
    # from app.models.follow import BlockedUser
    # blocked = await db.execute(
    #     select(BlockedUser).where(
    #         BlockerUser.blocker_id == post.user_id,
    #         BlockedUser.blocked_id == current_user.id
    #     )
    # ).scalar_one_or_none()
    # if blocked:
    #     raise HTTPException(status_code=403, detail="无权限评论该帖子")

    if body.parent_id:
        parent = await get_comment(db, body.parent_id)
        if not parent or parent.post_id != post_id:
            raise BusinessException("请求参数错误", code="VALIDATION_ERROR")
    comment = await create_comment(
        db,
        post_id=post_id,
        user_id=current_user.id,
        anonymous_name=current_user.anonymous_name,
        content=body.content,
        parent_id=body.parent_id,
    )
    # 异步风控检查
    background_tasks.add_task(run_risk_check_for_comment, comment.id)
    return success_response(data=CommentResponse.model_validate(comment).model_dump(), message="评论成功")


@router.delete("/comments/{comment_id}", status_code=204)
async def comment_delete(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除评论（仅本人可删）。"""
    comment = await get_comment(db, comment_id)
    if not comment:
        raise NotFoundException("资源不存在")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的评论")
    await delete_comment(db, comment_id)
    return None
