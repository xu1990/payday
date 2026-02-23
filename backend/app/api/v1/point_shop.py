"""积分商品API - Sprint 4.7 商品兑换系统"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import success_response
from app.models.user import User
from app.services.point_product_service import (
    # 商品管理
    create_product,
    update_product,
    delete_product,
    list_products,
    get_product,
    # 订单管理
    create_order,
    list_my_orders,
    get_order,
    cancel_order,
    list_all_orders,
    process_order,
)

router = APIRouter(prefix="/point-shop", tags=["point-shop"])


# ============== Schemas ==============
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    points_cost: int = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    stock_unlimited: bool = False
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    sort_order: int = 0


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    points_cost: Optional[int] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    stock_unlimited: Optional[bool] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class OrderCreate(BaseModel):
    product_id: str
    delivery_info: Optional[str] = None
    notes: Optional[str] = None


# ============== 用户端接口 ==============
@router.get("/products")
async def get_products(
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取商品列表"""
    products = await list_products(db, active_only=True, category=category)

    data = [{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "image_url": p.image_url,
        "points_cost": p.points_cost,
        "stock": p.stock if not p.stock_unlimited else 999,
        "stock_unlimited": p.stock_unlimited,
        "category": p.category,
    } for p in products]

    return success_response(data={"products": data, "total": len(data)})


@router.get("/products/{product_id}")
async def get_product_detail(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取商品详情"""
    product = await get_product(db, product_id)

    data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "image_url": product.image_url,
        "points_cost": product.points_cost,
        "stock": product.stock if not product.stock_unlimited else 999,
        "stock_unlimited": product.stock_unlimited,
        "category": product.category,
    }

    return success_response(data=data)


@router.post("/orders")
async def create_user_order(
    body: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """下单"""
    order = await create_order(
        db,
        current_user.id,
        body.product_id,
        body.delivery_info,
        body.notes,
    )

    data = {
        "id": order.id,
        "order_number": order.order_number,
        "product_name": order.product_name,
        "points_cost": order.points_cost,
        "status": order.status,
        "created_at": order.created_at.isoformat(),
    }

    return success_response(data=data, message="下单成功")


@router.get("/orders")
async def get_my_orders(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的订单列表"""
    orders = await list_my_orders(db, current_user.id, status, limit, offset)

    data = [{
        "id": o.id,
        "order_number": o.order_number,
        "product_name": o.product_name,
        "product_image": o.product_image,
        "points_cost": o.points_cost,
        "status": o.status,
        "created_at": o.created_at.isoformat(),
    } for o in orders]

    return success_response(data={"orders": data, "total": len(data)})


@router.get("/orders/{order_id}")
async def get_order_detail(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取订单详情"""
    order = await get_order(db, order_id, current_user.id)

    data = {
        "id": order.id,
        "order_number": order.order_number,
        "product_name": order.product_name,
        "product_image": order.product_image,
        "points_cost": order.points_cost,
        "delivery_info": order.delivery_info,
        "notes": order.notes,
        "status": order.status,
        "created_at": order.created_at.isoformat(),
    }

    return success_response(data=data)


@router.post("/orders/{order_id}/cancel")
async def cancel_user_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消订单"""
    order = await cancel_order(db, order_id, current_user.id)
    return success_response(message="订单已取消")


# ============== 管理员接口 ==============
@router.get("/admin/products")
async def admin_list_products(
    active_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有商品（管理员）"""
    products = await list_products(db, active_only=active_only)

    data = [{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "image_url": p.image_url,
        "points_cost": p.points_cost,
        "stock": p.stock,
        "stock_unlimited": p.stock_unlimited,
        "category": p.category,
        "is_active": p.is_active,
        "sort_order": p.sort_order,
        "created_at": p.created_at.isoformat(),
    } for p in products]

    return success_response(data={"products": data, "total": len(data)})


@router.post("/admin/products")
async def admin_create_product(
    body: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建商品（管理员）"""
    product = await create_product(
        db,
        body.name,
        body.points_cost,
        body.stock,
        body.stock_unlimited,
        body.description,
        body.image_url,
        body.category,
        body.sort_order,
    )

    return success_response(data={"id": product.id}, message="商品创建成功")


@router.put("/admin/products/{product_id}")
async def admin_update_product(
    product_id: str,
    body: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新商品（管理员）"""
    await update_product(db, product_id, **body.model_dump(exclude_unset=True))
    return success_response(message="商品更新成功")


@router.delete("/admin/products/{product_id}")
async def admin_delete_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除商品（管理员，软删除）"""
    await delete_product(db, product_id)
    return success_response(message="商品已删除")


@router.get("/admin/orders")
async def admin_list_orders(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有订单（管理员）"""
    orders = await list_all_orders(db, status, limit, offset)

    data = [{
        "id": o.id,
        "order_number": o.order_number,
        "user_id": o.user_id,
        "product_name": o.product_name,
        "points_cost": o.points_cost,
        "status": o.status,
        "created_at": o.created_at.isoformat(),
    } for o in orders]

    return success_response(data={"orders": data, "total": len(data)})


@router.post("/admin/orders/{order_id}/process")
async def admin_process_order(
    order_id: str,
    action: str = Body(..., description="complete or cancel"),
    notes: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """处理订单（管理员）"""
    order = await process_order(db, order_id, current_user.id, action, notes)
    return success_response(message=f"订单已{action}d")
