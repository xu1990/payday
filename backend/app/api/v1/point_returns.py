"""积分退货API - Sprint 4.7 商品兑换系统"""
import json
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user, get_current_user
from app.core.exceptions import BusinessException, NotFoundException, success_response
from app.models.user import User
from app.services.point_return_service import (approve_return, create_return, get_return,
                                               list_returns, reject_return)
from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/point-returns", tags=["point-returns"])


# ============== Schemas ==============
class ReturnCreate(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500, description="退货原因")


class ReturnApprove(BaseModel):
    admin_notes: Optional[str] = Field(None, max_length=500, description="管理员备注")


class ReturnReject(BaseModel):
    admin_notes: str = Field(..., min_length=1, max_length=500, description="拒绝原因")


# ============== 用户端接口 ==============
@router.post("/orders/{order_id}/return")
async def create_return_request(
    order_id: str,
    body: ReturnCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建退货申请"""
    return_request = await create_return(
        db,
        order_id,
        body.reason,
    )

    data = {
        "id": return_request.id,
        "order_id": return_request.order_id,
        "reason": return_request.reason,
        "status": return_request.status,
        "created_at": return_request.created_at.isoformat(),
    }

    return success_response(data=data, message="退货申请已提交")


@router.get("/{return_id}")
async def get_return_detail(
    return_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取退货申请详情（用户）"""
    return_request = await get_return(db, return_id)

    data = {
        "id": return_request.id,
        "order_id": return_request.order_id,
        "reason": return_request.reason,
        "status": return_request.status,
        "admin_notes": return_request.admin_notes,
        "created_at": return_request.created_at.isoformat(),
        "processed_at": return_request.processed_at.isoformat() if return_request.processed_at else None,
    }

    return success_response(data=data)


# ============== 管理员接口 ==============
@router.get("")
async def admin_list_returns(
    status: Optional[str] = Query(None, description="筛选状态"),
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取退货申请列表（管理员）"""
    returns = await list_returns(db, status, limit, offset)

    data = [{
        "id": r.id,
        "order_id": r.order_id,
        "reason": r.reason,
        "status": r.status,
        "admin_notes": r.admin_notes,
        "admin_id": r.admin_id,
        "created_at": r.created_at.isoformat(),
        "processed_at": r.processed_at.isoformat() if r.processed_at else None,
    } for r in returns]

    return success_response(data={"returns": data, "total": len(data)})


@router.get("/{return_id}")
async def admin_get_return_detail(
    return_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取退货申请详情（管理员）"""
    return_request = await get_return(db, return_id)

    data = {
        "id": return_request.id,
        "order_id": return_id,
        "reason": return_request.reason,
        "status": return_request.status,
        "admin_notes": return_request.admin_notes,
        "admin_id": return_request.admin_id,
        "created_at": return_request.created_at.isoformat(),
        "processed_at": return_request.processed_at.isoformat() if return_request.processed_at else None,
    }

    return success_response(data=data)


@router.post("/{return_id}/approve")
async def admin_approve_return(
    return_id: str,
    body: ReturnApprove,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """批准退货申请（管理员）"""
    admin_id = current_admin.id
    approved = await approve_return(
        db,
        return_id,
        admin_id,
        body.admin_notes,
    )

    data = {
        "id": approved.id,
        "status": approved.status,
        "admin_notes": approved.admin_notes,
        "processed_at": approved.processed_at.isoformat(),
    }

    return success_response(data=data, message="退货申请已批准")


@router.post("/{return_id}/reject")
async def admin_reject_return(
    return_id: str,
    body: ReturnReject,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """拒绝退货申请（管理员）"""
    admin_id = current_admin.id
    rejected = await reject_return(
        db,
        return_id,
        admin_id,
        body.admin_notes,
    )

    data = {
        "id": rejected.id,
        "status": rejected.status,
        "admin_notes": rejected.admin_notes,
        "processed_at": rejected.processed_at.isoformat(),
    }

    return success_response(data=data, message="退货申请已拒绝")