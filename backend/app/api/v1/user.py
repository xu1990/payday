"""
用户接口 - GET /me, PUT /me, GET /profile-data
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, File, UploadFile
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.core.exceptions import success_response, NotFoundException
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import update_user, get_user_profile_data, deactivate_user, reactivate_user, upload_user_avatar, get_user_by_id
from app.services.follow_service import is_following
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/user", tags=["user"])


def _user_to_response(user: User) -> dict:
    return {
        "id": user.id,
        "anonymous_name": user.anonymous_name,
        "nickname": user.nickname,
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


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return success_response(data=_user_to_response(current_user), message="获取用户信息成功")


@router.put("/me")
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await update_user(db, current_user.id, body)
    return success_response(data=_user_to_response(user), message="更新用户信息成功")


@router.get("/profile-data/{target_user_id}")
async def get_profile_data(
    target_user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户主页数据（帖子、打卡记录、粉丝数、关注数）"""
    # SECURITY: 验证target_user_id格式
    from app.utils.validation import validate_uuid
    validate_uuid(target_user_id, "target_user_id")

    data = await get_user_profile_data(db, current_user.id, target_user_id)
    return success_response(data=data, message="获取用户主页数据成功")


@router.post("/me/deactivate")
async def deactivate_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """注销当前用户账号（软删除，30天可恢复）"""
    user = await deactivate_user(db, current_user.id)
    recovery_until = (datetime.utcnow() + timedelta(days=30)).isoformat()

    return success_response(
        data={"recovery_until": recovery_until},
        message="注销成功，30天内可通过登录恢复"
    )


@router.post("/me/reactivate")
async def reactivate_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """恢复已注销的账号"""
    user = await reactivate_user(db, current_user.id)
    return success_response(data=_user_to_response(user), message="账号已恢复")


@router.post("/me/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传用户头像到腾讯云 COS"""
    from app.utils.storage import storage_service

    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        from app.core.exceptions import ValidationException
        raise ValidationException("只支持图片文件")

    # 读取文件内容
    content = await file.read()

    # 验证文件大小（5MB）
    if len(content) > 5 * 1024 * 1024:
        from app.core.exceptions import ValidationException
        raise ValidationException("图片大小不能超过5MB")

    # 上传到 COS
    import uuid
    ext = file.filename.split('.')[-1] if file.filename else 'jpg'
    key = f"avatars/{current_user.id}/{uuid.uuid4()}.{ext}"
    url = storage_service.cos_client.upload_file(content, key)

    # 更新用户头像
    user = await upload_user_avatar(db, current_user.id, url)

    return success_response(data={"url": url}, message="头像上传成功")


@router.get("/{user_id}/follow-status")
async def check_follow_status(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if current user is following target user."""
    if not await get_user_by_id(db, user_id):
        raise NotFoundException("资源不存在")

    following = await is_following(db, current_user.id, user_id)
    return success_response(data={"is_following": following}, message="获取关注状态成功")


class FeedbackCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="反馈内容")
    images: Optional[list[str]] = Field(None, description="反馈图片列表")
    contact: Optional[str] = Field(None, max_length=100, description="联系方式")


@router.post("/feedback")
async def submit_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交用户反馈"""
    from app.models.feedback import Feedback
    import uuid

    feedback = Feedback(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        content=data.content,
        images=data.images or [],
        contact=data.contact,
        status="pending"
    )

    db.add(feedback)
    await db.commit()

    return success_response(message="反馈已提交，感谢您的建议")
