"""邀请系统API - Sprint 4.7 邀请注册获取积分"""
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import success_response
from app.models.user import User
from app.services.invitation_service import (
    get_my_invite_code,
    get_invitation_stats,
    apply_invite_code,
    get_my_invitations,
)

router = APIRouter(prefix="/invitation", tags=["invitation"])


@router.get("/my-code")
async def get_my_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的邀请码"""
    code = await get_my_invite_code(db, current_user.id)
    return success_response(data={"invite_code": code}, message="获取邀请码成功")


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取邀请统计"""
    stats = await get_invitation_stats(db, current_user.id)
    return success_response(data=stats, message="获取统计信息成功")


@router.get("/my-invitations")
async def list_my_invitations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我邀请的用户列表"""
    invitations = await get_my_invitations(db, current_user.id, limit, offset)
    return success_response(
        data={"invitations": invitations, "total": len(invitations)},
        message="获取邀请列表成功"
    )


@router.post("/apply")
async def apply_code(
    invite_code: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    应用邀请码（注册时或个人中心调用）

    Body:
        {"invite_code": "ABCD1234"}
    """
    result = await apply_invite_code(db, current_user.id, invite_code)
    return success_response(
        data=result,
        message=f"邀请码应用成功，获得{result['points_earned']}积分"
    )
