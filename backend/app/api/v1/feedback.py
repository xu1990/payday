"""
反馈接口
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin_user
from app.core.exceptions import success_response
from app.models.user import User
from app.models.feedback import Feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="反馈内容")
    images: Optional[List[str]] = Field(None, max_length=3, description="反馈图片列表")
    contact: Optional[str] = Field(None, max_length=100, description="联系方式")


@router.post("/")
async def create_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交反馈"""
    feedback = Feedback(
        user_id=current_user.id,
        content=data.content,
        images=data.images,
        contact=data.contact
    )
    db.add(feedback)
    await db.commit()

    return success_response(message="反馈已提交，感谢您的建议")


@router.get("/")
async def list_feedbacks(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取反馈列表（管理员）"""
    from sqlalchemy import select

    result = await db.execute(
        select(Feedback).order_by(Feedback.created_at.desc())
    )
    feedbacks = result.scalars().all()

    items = []
    for f in feedbacks:
        items.append({
            "id": f.id,
            "user_id": f.user_id,
            "content": f.content,
            "images": f.images or [],
            "contact": f.contact,
            "status": f.status,
            "admin_reply": f.admin_reply,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        })

    return success_response(data=items, message="获取反馈列表成功")
