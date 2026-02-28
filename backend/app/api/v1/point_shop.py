"""积分商品API - Sprint 4.7 商品兑换系统"""
import json
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user, get_current_user
from app.core.exceptions import success_response
from app.models.address import UserAddress
from app.models.user import User
from app.services.point_product_service import (cancel_order, create_order,  # 商品管理; 订单管理
                                                create_product, delete_product, get_order,
                                                get_product, list_all_orders, list_my_orders,
                                                list_products, process_order, update_product)
from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

router = APIRouter(prefix="/point-shop", tags=["point-shop"])


# ============== Schemas ==============
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    points_cost: int = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    stock_unlimited: bool = False
    description: Optional[str] = None
    image_urls: Optional[List[str]] = Field(None, max_length=6)
    category: Optional[str] = None
    sort_order: int = 0
    has_sku: bool = False
    product_type: Literal["physical", "virtual", "bundle"] = "physical"
    shipping_method: Literal["express", "self_pickup", "no_shipping"] = "express"
    shipping_template_id: Optional[str] = None
    category_id: Optional[str] = None
    is_active: bool = True
    # SKU相关数据，创建时一起提交
    specifications: Optional[List[dict]] = Field(None, description="规格列表，如 [{'name': '颜色', 'values': ['红', '蓝']}]")
    skus: Optional[List[dict]] = Field(None, description="SKU列表，如 [{'specs': {'颜色': '红'}, 'stock': 10, 'points_cost': 100}]")


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    points_cost: Optional[int] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    stock_unlimited: Optional[bool] = None
    description: Optional[str] = None
    image_urls: Optional[List[str]] = Field(None, max_length=6)
    category: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    has_sku: Optional[bool] = None
    product_type: Optional[Literal["physical", "virtual", "bundle"]] = None
    shipping_method: Optional[Literal["express", "self_pickup", "no_shipping"]] = None
    shipping_template_id: Optional[str] = None
    category_id: Optional[str] = None


class OrderCreate(BaseModel):
    product_id: str
    address_id: Optional[str] = None
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
    from app.models.point_category import PointCategory

    products = await list_products(db, active_only=True, category=category)

    # 批量查询所有需要的分类
    category_ids = [p.category_id for p in products if p.category_id]
    category_map = {}
    if category_ids:
        result = await db.execute(
            select(PointCategory).where(PointCategory.id.in_(category_ids))
        )
        for cat in result.scalars().all():
            category_map[str(cat.id)] = cat.name

    data = []
    for p in products:
        # 解析图片URLs
        image_urls = []
        if p.image_urls:
            try:
                image_urls = json.loads(p.image_urls)
            except:
                pass

        # 获取分类名称：优先使用分类表中的名称，其次使用商品自身的category字段
        category_name = p.category
        if p.category_id and str(p.category_id) in category_map:
            category_name = category_map[str(p.category_id)]

        data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "image_urls": image_urls,
            "image_url": image_urls[0] if image_urls else None,  # 兼容旧版
            "points_cost": p.points_cost,
            "stock": p.stock if not p.stock_unlimited else 999,
            "stock_unlimited": p.stock_unlimited,
            "category": category_name,
        })

    return success_response(data={"products": data, "total": len(data)})


@router.get("/products/{product_id}")
async def get_product_detail(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取商品详情"""
    product = await get_product(db, product_id)

    # 解析图片URLs
    image_urls = []
    if product.image_urls:
        try:
            image_urls = json.loads(product.image_urls)
        except:
            pass

    data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "image_urls": image_urls,
        "image_url": image_urls[0] if image_urls else None,  # 兼容旧版
        "points_cost": product.points_cost,
        "stock": product.stock if not product.stock_unlimited else 999,
        "stock_unlimited": product.stock_unlimited,
        "category": product.category,
        "category_id": str(product.category_id) if product.category_id else None,
        "has_sku": product.has_sku,
        "product_type": product.product_type,
        "shipping_method": product.shipping_method,
        "shipping_template_id": str(product.shipping_template_id) if product.shipping_template_id else None,
    }

    # 如果商品启用SKU管理,加载SKU列表和规格列表
    if product.has_sku:
        from app.services.point_sku_service import list_skus, list_specifications

        # 加载规格列表
        specs = await list_specifications(db, product_id)
        from app.schemas.point_sku import SpecificationResponse
        specifications = []
        for spec in specs:
            # 加载每个规格的值列表
            from app.services.point_sku_service import list_specification_values
            from app.schemas.point_sku import SpecificationValueResponse

            spec_values = await list_specification_values(db, spec.id)
            values_data = [SpecificationValueResponse.from_db(v) for v in spec_values]

            spec_data = SpecificationResponse.from_db(spec)
            specifications.append({
                **spec_data.model_dump(),
                "values": [v.model_dump() for v in values_data]
            })

        # 加载SKU列表
        skus = await list_skus(db, product_id, active_only=True)
        from app.schemas.point_sku import SKUResponse
        skus_data = [SKUResponse.from_db(sku) for sku in skus]

        data["specifications"] = specifications
        data["skus"] = [sku.model_dump() for sku in skus_data]

    # 如果商品有运费模板，加载运费模板信息
    if product.shipping_template_id:
        from app.services.shipping_service import ShippingTemplateService
        service = ShippingTemplateService(db)
        template = await service.get_template(str(product.shipping_template_id))
        if template:
            # 获取不配送区域
            excluded_regions = template.excluded_regions or []

            # 获取模板区域配置中的不配送区域
            regions = await service.list_regions(str(product.shipping_template_id))
            excluded_region_names = []
            delivery_region_names = []
            for region in regions:
                if region.is_excluded:
                    excluded_region_names.append(region.region_names)
                else:
                    delivery_region_names.append(region.region_names)

            data["shipping_template"] = {
                "id": str(template.id),
                "name": template.name,
                "charge_type": template.charge_type,
                "free_shipping_type": template.free_shipping_type,
                "excluded_regions": excluded_regions,
                "excluded_region_names": excluded_region_names,
                "delivery_region_names": delivery_region_names,
                "estimate_days_min": template.estimate_days_min,
                "estimate_days_max": template.estimate_days_max,
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
        body.address_id,
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

    # 查询收货地址
    address = None
    if order.address_id:
        result = await db.execute(
            select(UserAddress).where(UserAddress.id == order.address_id)
        )
        addr = result.scalar_one_or_none()
        if addr:
            address = {
                "id": addr.id,
                "contact_name": addr.contact_name,
                "contact_phone": addr.contact_phone,
                "province_name": addr.province_name,
                "city_name": addr.city_name,
                "district_name": addr.district_name,
                "detailed_address": addr.detailed_address,
            }

    data = {
        "id": order.id,
        "order_number": order.order_number,
        "product_name": order.product_name,
        "product_image": order.product_image,
        "points_cost": order.points_cost,
        "delivery_info": order.delivery_info,
        "notes": order.notes,
        "notes_admin": order.notes_admin,
        "status": order.status,
        "address": address,
        "shipment_id": order.shipment_id,
        "created_at": order.created_at.isoformat(),
        "processed_at": order.processed_at.isoformat() if order.processed_at else None,
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
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有商品（管理员）"""
    from app.models.point_category import PointCategory

    products = await list_products(db, active_only=active_only)

    # 批量查询所有需要的分类
    category_ids = [p.category_id for p in products if p.category_id]
    category_map = {}
    if category_ids:
        result = await db.execute(
            select(PointCategory).where(PointCategory.id.in_(category_ids))
        )
        for cat in result.scalars().all():
            category_map[str(cat.id)] = cat.name

    data = []
    for p in products:
        # 解析图片URLs
        image_urls = []
        if p.image_urls:
            try:
                image_urls = json.loads(p.image_urls)
            except:
                pass

        # 获取分类名称：优先使用分类表中的名称，其次使用商品自身的category字段
        category_name = p.category
        if p.category_id and str(p.category_id) in category_map:
            category_name = category_map[str(p.category_id)]

        data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "image_urls": image_urls,
            "image_url": image_urls[0] if image_urls else None,  # 兼容旧版
            "points_cost": p.points_cost,
            "stock": p.stock,
            "stock_unlimited": p.stock_unlimited,
            "category": category_name,
            "category_id": str(p.category_id) if p.category_id else None,
            "has_sku": p.has_sku,
            "product_type": p.product_type,
            "shipping_method": p.shipping_method,
            "shipping_template_id": str(p.shipping_template_id) if p.shipping_template_id else None,
            "is_active": p.is_active,
            "sort_order": p.sort_order,
            "created_at": p.created_at.isoformat(),
        })

    return success_response(data={"products": data, "total": len(data)})


@router.post("/admin/products")
async def admin_create_product(
    body: ProductCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建商品（管理员）- 支持一起提交SKU信息"""
    import uuid
    from app.models.point_sku import PointProductSKU, PointSpecification, PointSpecificationValue

    # 创建商品
    product = await create_product(
        db,
        body.name,
        body.points_cost,
        body.stock,
        body.stock_unlimited,
        body.description,
        body.image_urls,
        body.category,
        body.sort_order,
        has_sku=body.has_sku,
        product_type=body.product_type,
        shipping_method=body.shipping_method,
        shipping_template_id=body.shipping_template_id,
        category_id=body.category_id,
        is_active=body.is_active,
    )

    # 如果是SKU商品，一起创建规格和SKU
    if body.has_sku and body.specifications and body.skus:
        # 创建规格和规格值
        spec_id_map = {}  # 规格名 -> 规格ID
        spec_value_id_map = {}  # (规格名, 规格值) -> 规格值ID

        for spec_data in body.specifications:
            spec_name = spec_data.get("name", "")
            spec_values = spec_data.get("values", [])

            if not spec_name:
                continue

            # 创建规格
            spec = PointSpecification(
                product_id=product.id,
                name=spec_name,
                sort_order=spec_data.get("sort_order", 0),
            )
            db.add(spec)
            await db.flush()
            spec_id_map[spec_name] = spec.id

            # 创建规格值
            for idx, value in enumerate(spec_values):
                if not value or not str(value).strip():
                    continue
                spec_value = PointSpecificationValue(
                    specification_id=spec.id,
                    value=str(value).strip(),
                    sort_order=idx,
                )
                db.add(spec_value)
                await db.flush()
                spec_value_id_map[(spec_name, str(value).strip())] = spec_value.id

        # 创建SKU
        for idx, sku_data in enumerate(body.skus):
            specs_dict = sku_data.get("specs", {})
            if not specs_dict:
                continue

            # 生成SKU编码
            sku_code = sku_data.get("sku_code") or f"SKU-{product.id[:8]}-{idx+1}"

            # 创建SKU
            sku = PointProductSKU(
                product_id=product.id,
                sku_code=sku_code,
                specs=json.dumps(specs_dict, ensure_ascii=False),
                points_cost=sku_data.get("points_cost", body.points_cost),
                stock=sku_data.get("stock", 0),
                stock_unlimited=sku_data.get("stock_unlimited", False),
                image_url=sku_data.get("image_url"),
                sort_order=sku_data.get("sort_order", idx),
                is_active=sku_data.get("is_active", True),
            )
            db.add(sku)

        await db.commit()

    return success_response(data={"id": product.id}, message="商品创建成功")


@router.get("/admin/products/{product_id}")
async def admin_get_product(
    product_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个商品详情（管理员）"""
    product = await get_product(db, product_id)

    # 解析图片URLs
    image_urls = []
    if product.image_urls:
        try:
            image_urls = json.loads(product.image_urls)
        except:
            pass

    data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "image_urls": image_urls,
        "image_url": image_urls[0] if image_urls else None,
        "points_cost": product.points_cost,
        "stock": product.stock,
        "stock_unlimited": product.stock_unlimited,
        "category": product.category,
        "category_id": product.category_id,
        "has_sku": product.has_sku,
        "product_type": product.product_type,
        "shipping_method": product.shipping_method,
        "shipping_template_id": product.shipping_template_id,
        "is_active": product.is_active,
        "sort_order": product.sort_order,
        "created_at": product.created_at.isoformat(),
    }

    return success_response(data=data)


@router.put("/admin/products/{product_id}")
async def admin_update_product(
    product_id: str,
    body: ProductUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新商品（管理员）"""
    await update_product(db, product_id, **body.model_dump(exclude_unset=True))
    return success_response(message="商品更新成功")


@router.delete("/admin/products/{product_id}")
async def admin_delete_product(
    product_id: str,
    current_admin: User = Depends(get_current_admin_user),
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
    current_admin: User = Depends(get_current_admin_user),
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
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """处理订单（管理员）"""
    order = await process_order(db, order_id, current_admin.id, action, notes)
    return success_response(message=f"订单已{action}d")
