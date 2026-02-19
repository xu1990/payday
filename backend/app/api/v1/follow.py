"""
关注接口 - 关注/取关、粉丝列表、关注列表；与技术方案 3.3.2 一致
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import NotFoundException, AuthorizationException, success_response
from app.models.user import User
from app.schemas.follow import FollowActionResponse, FollowListResponse
from app.schemas.user import UserResponse
from app.schemas.post import PostResponse
from app.services.follow_service import (
    count_following_posts,
    follow_user,
    unfollow_user,
    get_followers,
    get_following,
    is_following,
    list_following_posts,
)
from app.services.user_service import get_user_by_id

router = APIRouter(prefix="/user", tags=["follow"])


def _user_to_response(user: User) -> dict:
    return {
        "id": user.id,
        "anonymous_name": user.anonymous_name,
        "avatar": user.avatar,
        "bio": user.bio,
        "follower_count": user.follower_count or 0,
        "following_count": user.following_count or 0,
        "post_count": user.post_count or 0,
        "allow_follow": user.allow_follow,
        "allow_comment": user.allow_comment,
        "status": user.status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.post("/{user_id}/follow")
async def follow(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = await get_user_by_id(db, user_id)
    if not target:
        raise NotFoundException("资源不存在")
    if target.allow_follow == 0:
        raise AuthorizationException("无权限访问")
    ok = await follow_user(db, current_user.id, user_id)
    return success_response(data={"ok": ok, "following": True}, message="关注成功")


@router.delete("/{user_id}/follow")
async def unfollow(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await unfollow_user(db, current_user.id, user_id)
    return success_response(data={"ok": ok, "following": False}, message="取消关注成功")


@router.get("/me/followers")
async def my_followers(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    users, total = await get_followers(db, current_user.id, limit=limit, offset=offset)
    data = {
        "items": [_user_to_response(u) for u in users],
        "total": total,
    }
    return success_response(data=data, message="获取粉丝列表成功")


@router.get("/me/feed")
async def my_feed(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """关注流：当前用户关注的人发布的帖子（与 PRD 5.1.7、技术方案 3.3.2 一致）。"""
    total = await count_following_posts(db, current_user.id)
    posts = await list_following_posts(db, current_user.id, limit=limit, offset=offset)
    data = {
        "items": [PostResponse.model_validate(p).model_dump(mode='json') for p in posts],
        "total": total,
    }
    return success_response(data=data, message="获取关注流成功")


@router.get("/me/following")
async def my_following(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    users, total = await get_following(db, current_user.id, limit=limit, offset=offset)
    data = {
        "items": [_user_to_response(u) for u in users],
        "total": total,
    }
    return success_response(data=data, message="获取关注列表成功")


@router.get("/{user_id}/followers")
async def user_followers(
    user_id: str,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    if not await get_user_by_id(db, user_id):
        raise NotFoundException("资源不存在")
    users, total = await get_followers(db, user_id, limit=limit, offset=offset)
    data = {
        "items": [_user_to_response(u) for u in users],
        "total": total,
    }
    return success_response(data=data, message="获取粉丝列表成功")


@router.get("/{user_id}/following")
async def user_following(
    user_id: str,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    if not await get_user_by_id(db, user_id):
        raise NotFoundException("资源不存在")
    users, total = await get_following(db, user_id, limit=limit, offset=offset)
    data = {
        "items": [_user_to_response(u) for u in users],
        "total": total,
    }
    return success_response(data=data, message="获取关注列表成功")
