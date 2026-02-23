"""Ability Points API - 能力值系统接口（Sprint 4.6）"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.core.exceptions import success_response
from app.models.user import User
from app.models.admin import AdminUser
from app.schemas.ability_points import (
    AbilityPointResponse,
    AbilityPointTransactionResponse,
    PointRedemptionCreate,
    PointRedemptionResponse,
    PointRedemptionUpdate,
    AdminRedemptionListResponse,
)
from app.services.ability_points_service import (
    get_or_create_user_points,
    get_user_transactions,
    create_redemption,
    get_user_redemptions,
    get_all_redemptions,
    update_redemption_status,
    trigger_event,
    POINT_EVENTS,
)

router = APIRouter(prefix="/ability-points", tags=["ability-points"])


# ============== 用户端接口 ==============
@router.get("/my")
async def get_my_points(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的积分信息"""
    points = await get_or_create_user_points(db, current_user.id)
    response = AbilityPointResponse(**points.__dict__)
    return success_response(data=response.model_dump(mode='json'))


@router.get("/my/transactions")
async def get_my_transactions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的积分流水"""
    transactions = await get_user_transactions(db, current_user.id, limit, offset)
    response = [AbilityPointTransactionResponse(**t.__dict__).model_dump(mode='json') for t in transactions]
    return success_response(data={"transactions": response, "total": len(response)})


@router.post("/redemptions")
async def create_redeem(
    body: PointRedemptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建积分兑换"""
    redemption = await create_redemption(db, current_user.id, body)
    response = PointRedemptionResponse(**redemption.__dict__)
    return success_response(data=response.model_dump(mode='json'), message="兑换申请已提交，等待审核")


@router.get("/redemptions")
async def get_my_redemptions(
    status: str = Query(None, description="筛选状态"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的兑换记录"""
    redemptions = await get_user_redemptions(db, current_user.id, status)
    response = [PointRedemptionResponse(**r.__dict__).model_dump(mode='json') for r in redemptions]
    return success_response(data={"redemptions": response, "total": len(response)})


@router.get("/events")
async def list_point_events():
    """获取积分事件列表（展示所有可获得积分的事件）"""
    events = [{"event_type": k, "points": v} for k, v in POINT_EVENTS.items()]
    return success_response(data={"events": events, "total": len(events)})


# ============== 管理员接口 ==============
@router.get("/admin/redemptions")
async def admin_get_redemptions(
    status: str = Query(None, description="筛选状态"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取所有兑换记录（管理员）"""
    redemptions = await get_all_redemptions(db, status, limit, offset)
    pending = await get_all_redemptions(db, "pending", 1000, 0)  # 获取待处理数量

    response_list = [PointRedemptionResponse(**r.__dict__).model_dump(mode='json') for r in redemptions]
    response = AdminRedemptionListResponse(
        redemptions=response_list,
        total=len(response_list),
        pending_count=len([r for r in pending if r.status == "pending"]),
    )
    return success_response(data=response.model_dump(mode='json'))


@router.put("/admin/redemptions/{redemption_id}")
async def admin_update_redemption(
    redemption_id: str,
    body: PointRedemptionUpdate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """处理兑换申请（管理员）"""
    redemption = await update_redemption_status(db, redemption_id, current_admin.id, body)
    response = PointRedemptionResponse(**redemption.__dict__)
    return success_response(data=response.model_dump(mode='json'), message=f"兑换已{body.status}")
