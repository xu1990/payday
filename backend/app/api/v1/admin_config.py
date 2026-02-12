"""
会员与主题配置接口 - 管理后台
"""
from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.models.user import User
from app.models.membership import Membership, AppTheme
from app.schemas.membership import MembershipCreate, MembershipResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/admin/config", tags=["admin-config"])


# ==================== 主题管理 ====================

class ThemeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    preview_image: str | None = Field(None, max_length=500)
    config: str | None = Field(None)
    is_premium: bool = False
    sort_order: int = Field(0, ge=0)


class ThemeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    preview_image: str | None = Field(None, max_length=500)
    config: str | None = None
    is_premium: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(None, ge=0)


class ThemeResponse(BaseModel):
    id: str
    name: str
    code: str
    preview_image: str | None
    config: str | None
    is_premium: bool
    is_active: bool
    sort_order: int
    created_at: str

    class Config:
        from_attributes = True


@router.get("/themes", response_model=list[ThemeResponse])
async def list_themes(
    active_only: bool = Query(False),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取主题列表。"""
    from sqlalchemy import select

    q = select(AppTheme)
    if active_only:
        q = q.where(AppTheme.is_active == True)
    q = q.order_by(AppTheme.sort_order.desc(), AppTheme.created_at.desc())
    result = await db.execute(q)
    themes = list(result.scalars().all())
    return [ThemeResponse.model_validate(t) for t in themes]


@router.post("/themes", response_model=ThemeResponse)
async def create_theme(
    data: ThemeCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建主题。"""
    theme = AppTheme(**data.model_dump())
    db.add(theme)
    await db.flush()
    await db.refresh(theme)
    return ThemeResponse.model_validate(theme)


@router.put("/themes/{theme_id}", response_model=ThemeResponse)
async def update_theme(
    theme_id: str,
    data: ThemeUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新主题。"""
    from sqlalchemy import select, update

    result = await db.execute(select(AppTheme).where(AppTheme.id == theme_id))
    theme = result.scalar_one_or_none()
    if not theme:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="主题不存在")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    await db.execute(
        update(AppTheme).where(AppTheme.id == theme_id).values(**update_data)
    )
    await db.commit()
    await db.refresh(theme)
    return ThemeResponse.model_validate(theme)


@router.delete("/themes/{theme_id}")
async def delete_theme(
    theme_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除主题。"""
    from sqlalchemy import delete

    result = await db.execute(delete(AppTheme).where(AppTheme.id == theme_id))
    await db.commit()
    return {"deleted": result.rowcount > 0}


# ==================== 会员套餐管理 ====================

class MembershipListResponse(BaseModel):
    items: list[MembershipResponse]
    total: int


@router.get("/memberships", response_model=MembershipListResponse)
async def list_memberships(
    active_only: bool = Query(False),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取会员套餐列表。"""
    from sqlalchemy import select, func

    q = select(Membership)
    if active_only:
        q = q.where(Membership.is_active == 1)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(Membership.sort_order.desc(), Membership.created_at.desc())
    result = await db.execute(q)
    items = list(result.scalars().all())
    return MembershipListResponse(
        items=[MembershipResponse.model_validate(m) for m in items], total=total
    )


@router.post("/memberships", response_model=MembershipResponse)
async def create_membership(
    data: MembershipCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建会员套餐。"""
    membership = Membership(**data.model_dump())
    db.add(membership)
    await db.flush()
    await db.refresh(membership)
    return MembershipResponse.model_validate(membership)


@router.put("/memberships/{membership_id}", response_model=MembershipResponse)
async def update_membership(
    membership_id: str,
    data: MembershipCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新会员套餐。"""
    from sqlalchemy import select, update

    result = await db.execute(
        select(Membership).where(Membership.id == membership_id)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="套餐不存在")

    update_data = data.model_dump()
    await db.execute(
        update(Membership)
        .where(Membership.id == membership_id)
        .values(**update_data)
    )
    await db.commit()
    await db.refresh(membership)
    return MembershipResponse.model_validate(membership)


@router.delete("/memberships/{membership_id}")
async def delete_membership(
    membership_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除会员套餐。"""
    from sqlalchemy import delete

    result = await db.execute(
        delete(Membership).where(Membership.id == membership_id)
    )
    await db.commit()
    return {"deleted": result.rowcount > 0}
