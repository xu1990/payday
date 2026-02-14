"""
用户接口 - GET /me, PUT /me, GET /profile-data
"""
from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user, verify_csrf_token
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import update_user, get_user_profile_data
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/user", tags=["user"])


def _user_to_response(user: User) -> dict:
    return {
        "id": user.id,
        "anonymous_name": user.anonymous_name,
        "avatar": user.avatar,
        "bio": user.bio,
        "follower_count": user.follower_count,
        "following_count": user.following_count,
        "post_count": user.post_count,
        "allow_follow": user.allow_follow,
        "allow_comment": user.allow_comment,
        "status": user.status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(**_user_to_response(current_user))


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    _csrf: bool = Depends(verify_csrf_token),  # 添加 CSRF 保护
    db: AsyncSession = Depends(get_db),
):
    user = await update_user(db, current_user.id, body)
    return UserResponse(**_user_to_response(user))


@router.get("/profile-data/{target_user_id}")
async def get_profile_data(
    target_user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户主页数据（帖子、打卡记录、粉丝数、关注数）"""
    data = await get_user_profile_data(db, current_user.id, target_user_id)
    return data
