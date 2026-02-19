"""
会员与主题配置接口 - 管理后台
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import success_response, NotFoundException
from app.models.user import User
from app.models.membership import Membership, AppTheme, MembershipOrder
from app.models.miniprogram_config import MiniprogramConfig
from app.schemas.membership import MembershipCreate, MembershipResponse

router = APIRouter(prefix="/admin/config", tags=["admin-config"])


# ==================== 主题管理 ====================

class ThemeCreate(BaseModel):
    name: str
    code: str
    preview_image: Optional[str] = None
    config: Optional[str] = None
    is_premium: bool = False
    sort_order: int = 0


class ThemeUpdate(BaseModel):
    name: Optional[str] = None
    preview_image: Optional[str] = None
    config: Optional[str] = None
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("/themes")
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

    items = []
    for t in themes:
        items.append({
            "id": t.id,
            "name": t.name,
            "code": t.code,
            "preview_image": t.preview_image,
            "config": t.config,
            "is_premium": bool(t.is_premium),
            "is_active": bool(t.is_active),
            "sort_order": t.sort_order,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return success_response(data=items, message="获取主题列表成功")


@router.post("/themes")
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

    result = {
        "id": theme.id,
        "name": theme.name,
        "code": theme.code,
        "preview_image": theme.preview_image,
        "config": theme.config,
        "is_premium": bool(theme.is_premium),
        "is_active": bool(theme.is_active),
        "sort_order": theme.sort_order,
        "created_at": theme.created_at.isoformat() if theme.created_at else None,
    }

    return success_response(data=result, message="创建主题成功")


@router.put("/themes/{theme_id}")
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
        raise NotFoundException("资源不存在")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    await db.execute(
        update(AppTheme).where(AppTheme.id == theme_id).values(**update_data)
    )
    await db.commit()
    await db.refresh(theme)

    response_data = {
        "id": theme.id,
        "name": theme.name,
        "code": theme.code,
        "preview_image": theme.preview_image,
        "config": theme.config,
        "is_premium": bool(theme.is_premium),
        "is_active": bool(theme.is_active),
        "sort_order": theme.sort_order,
        "created_at": theme.created_at.isoformat() if theme.created_at else None,
    }

    return success_response(data=response_data, message="更新主题成功")


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
    return success_response(data={"deleted": result.rowcount > 0}, message="删除主题成功")


# ==================== 会员套餐管理 ====================

@router.get("/memberships")
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

    items_data = [MembershipResponse.model_validate(m).model_dump(mode='json') for m in items]

    return success_response(
        data={"items": items_data, "total": total},
        message="获取会员套餐列表成功"
    )


@router.post("/memberships")
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

    return success_response(
        data=MembershipResponse.model_validate(membership).model_dump(mode='json'),
        message="创建会员套餐成功"
    )


@router.put("/memberships/{membership_id}")
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
        raise NotFoundException("资源不存在")

    update_data = data.model_dump()
    await db.execute(
        update(Membership)
        .where(Membership.id == membership_id)
        .values(**update_data)
    )
    await db.commit()
    await db.refresh(membership)

    return success_response(
        data=MembershipResponse.model_validate(membership).model_dump(mode='json'),
        message="更新会员套餐成功"
    )


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

    return success_response(data={"deleted": result.rowcount > 0}, message="删除会员套餐成功")


# ==================== 会员订单管理 ====================

class OrderStatusUpdate(BaseModel):
    status: str  # pending | paid | cancelled | refunded


@router.get("/orders")
async def list_orders(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取会员订单列表。"""
    from sqlalchemy import select, func

    q = select(MembershipOrder)
    # 关联会员套餐名称
    q = q.join(Membership, MembershipOrder.membership_id == Membership.id)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(MembershipOrder.created_at.desc())
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    orders = list(result.scalars().all())

    # 构建响应，包含套餐名称
    items = []
    for order in orders:
        # 获取套餐名称
        membership_result = await db.execute(
            select(Membership).where(Membership.id == order.membership_id)
        )
        membership = membership_result.scalar_one_or_none()

        item = {
            "id": order.id,
            "user_id": order.user_id,
            "membership_id": order.membership_id,
            "membership_name": membership.name if membership else "未知套餐",
            "amount": float(order.amount),
            "status": order.status,
            "payment_method": order.payment_method,
            "transaction_id": order.transaction_id,
            "start_date": order.start_date.isoformat() if order.start_date else None,
            "end_date": order.end_date.isoformat() if order.end_date else None,
            "auto_renew": bool(order.auto_renew),
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }
        items.append(item)

    return success_response(
        data={"items": items, "total": total},
        message="获取订单列表成功"
    )


@router.put("/orders/{order_id}")
async def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新订单状态。"""
    from sqlalchemy import select, update

    result = await db.execute(
        select(MembershipOrder).where(MembershipOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("资源不存在")

    await db.execute(
        update(MembershipOrder)
        .where(MembershipOrder.id == order_id)
        .values(status=data.status)
    )
    await db.commit()

    return success_response(data={"updated": True}, message="更新订单状态成功")


# ==================== 小程序配置管理 ====================

class MiniprogramConfigCreate(BaseModel):
    key: str = Field(..., max_length=50, description="配置键")
    value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, max_length=200, description="配置说明")
    sort_order: int = Field(0, description="排序")


class MiniprogramConfigUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("/miniprogram")
async def list_miniprogram_configs(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取小程序配置列表。"""
    from sqlalchemy import select

    q = select(MiniprogramConfig).order_by(MiniprogramConfig.sort_order.desc(), MiniprogramConfig.created_at.desc())
    result = await db.execute(q)
    configs = list(result.scalars().all())

    items = []
    for c in configs:
        items.append({
            "id": c.id,
            "key": c.key,
            "value": c.value,
            "description": c.description,
            "is_active": bool(c.is_active),
            "sort_order": c.sort_order,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })

    return success_response(data=items, message="获取小程序配置列表成功")


@router.post("/miniprogram")
async def create_miniprogram_config(
    data: MiniprogramConfigCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建小程序配置。"""
    from sqlalchemy import select

    # 检查 key 是否已存在
    result = await db.execute(select(MiniprogramConfig).where(MiniprogramConfig.key == data.key))
    if result.scalar_one_or_none():
        return success_response(data=None, message="配置键已存在", code="KEY_EXISTS")

    config = MiniprogramConfig(**data.model_dump())
    db.add(config)
    await db.flush()
    await db.refresh(config)

    result_data = {
        "id": config.id,
        "key": config.key,
        "value": config.value,
        "description": config.description,
        "is_active": bool(config.is_active),
        "sort_order": config.sort_order,
        "created_at": config.created_at.isoformat() if config.created_at else None,
    }

    return success_response(data=result_data, message="创建小程序配置成功")


@router.put("/miniprogram/{config_id}")
async def update_miniprogram_config(
    config_id: str,
    data: MiniprogramConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新小程序配置。"""
    from sqlalchemy import select, update

    result = await db.execute(select(MiniprogramConfig).where(MiniprogramConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise NotFoundException("配置不存在")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    await db.execute(
        update(MiniprogramConfig).where(MiniprogramConfig.id == config_id).values(**update_data)
    )
    await db.commit()
    await db.refresh(config)

    response_data = {
        "id": config.id,
        "key": config.key,
        "value": config.value,
        "description": config.description,
        "is_active": bool(config.is_active),
        "sort_order": config.sort_order,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }

    return success_response(data=response_data, message="更新小程序配置成功")


@router.delete("/miniprogram/{config_id}")
async def delete_miniprogram_config(
    config_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除小程序配置。"""
    from sqlalchemy import delete

    result = await db.execute(delete(MiniprogramConfig).where(MiniprogramConfig.id == config_id))
    await db.commit()
    return success_response(data={"deleted": result.rowcount > 0}, message="删除小程序配置成功")


# ==================== 协议管理 ====================

class AgreementUpdate(BaseModel):
    type: str = Field(..., description="协议类型: user 或 privacy")
    content: str = Field(..., description="协议内容（HTML）")


@router.get("/agreements")
async def get_agreements(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户协议和隐私协议"""
    from sqlalchemy import select

    # 获取用户协议
    user_result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'user_agreement')
    )
    user_config = user_result.scalar_one_or_none()

    # 获取隐私协议
    privacy_result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'privacy_agreement')
    )
    privacy_config = privacy_result.scalar_one_or_none()

    return success_response(
        data={
            "user_agreement": user_config.value if user_config else "",
            "privacy_agreement": privacy_config.value if privacy_config else "",
            "updated_at": (
                max(user_config.updated_at, privacy_config.updated_at).isoformat()
                if user_config and privacy_config
                else None
            )
        },
        message="获取协议成功"
    )


@router.post("/agreements")
async def update_agreement(
    data: AgreementUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新协议内容"""
    from sqlalchemy import select, update

    key = f"{data.type}_agreement"

    # 查找现有配置
    result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == key)
    )
    config = result.scalar_one_or_none()

    if config:
        # 更新现有配置
        await db.execute(
            update(MiniprogramConfig)
            .where(MiniprogramConfig.key == key)
            .values(value=data.content)
        )
    else:
        # 创建新配置
        new_config = MiniprogramConfig(
            key=key,
            value=data.content,
            description=f"{data.type} agreement",
            is_active=True,
            sort_order=0
        )
        db.add(new_config)

    await db.commit()

    return success_response(message="保存成功")


# ==================== 开屏配置管理 ====================

class SplashConfigUpdate(BaseModel):
    image_url: str = Field(..., description="开屏图片 URL")
    content: str = Field(..., description="欢迎文字")
    countdown: int = Field(3, ge=1, le=10, description="倒计时时长（秒）")
    is_active: bool = Field(True, description="是否启用")


@router.get("/splash")
async def get_splash_config(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取开屏配置"""
    from sqlalchemy import select
    import json

    result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'splash_config')
    )
    config = result.scalar_one_or_none()

    if not config or not config.value:
        return success_response(
            data={
                "image_url": "",
                "content": "",
                "countdown": 3,
                "is_active": False
            },
            message="获取开屏配置成功"
        )

    try:
        splash_data = json.loads(config.value)
        return success_response(
            data={
                "image_url": splash_data.get("image_url", ""),
                "content": splash_data.get("content", ""),
                "countdown": splash_data.get("countdown", 3),
                "is_active": config.is_active
            },
            message="获取开屏配置成功"
        )
    except (json.JSONDecodeError, TypeError):
        return success_response(
            data={
                "image_url": "",
                "content": "",
                "countdown": 3,
                "is_active": False
            },
            message="开屏配置格式错误"
        )


@router.post("/splash")
async def update_splash_config(
    data: SplashConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新开屏配置"""
    from sqlalchemy import select, update
    import json

    # 查找现有配置
    result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'splash_config')
    )
    config = result.scalar_one_or_none()

    value_json = json.dumps({
        "image_url": data.image_url,
        "content": data.content,
        "countdown": data.countdown,
    })

    if config:
        # 更新现有配置
        await db.execute(
            update(MiniprogramConfig)
            .where(MiniprogramConfig.key == 'splash_config')
            .values(value=value_json, is_active=data.is_active)
        )
    else:
        # 创建新配置
        new_config = MiniprogramConfig(
            key='splash_config',
            value=value_json,
            description='Splash screen configuration',
            is_active=data.is_active,
            sort_order=0
        )
        db.add(new_config)

    await db.commit()

    return success_response(message="保存成功")