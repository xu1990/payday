"""积分商品API - Sprint 4.7 商品兑换系统"""
import json
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user, get_current_user, rate_limit_point_order
from app.core.exceptions import BusinessException, NotFoundException, success_response
from app.models.address import UserAddress
from app.models.point_sku import PointProductSKU, PointSpecification, PointSpecificationValue
from app.models.user import User
from app.schemas.point_product import PointProductUpdate as ProductUpdate
from app.services.point_product_service import (cancel_order, create_order,  # 商品管理; 订单管理
                                                create_product, delete_product, get_order,
                                                get_product, list_all_orders, list_my_orders,
                                                list_products, process_order, update_product)
from app.utils.distributed_lock import CombinedLock
from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
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
    fake_sold: int = Field(0, ge=0, description="注水销量（虚拟销量）")
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
    fake_sold: Optional[int] = Field(None, ge=0, description="注水销量")
    off_shelf_reason: Optional[str] = Field(None, max_length=255, description="下架原因")


class OffShelfRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=255, description="下架/删除原因")


class OrderCreate(BaseModel):
    product_id: str
    sku_id: Optional[str] = None  # SKU ID（多规格商品时需要）
    address_id: Optional[str] = None
    delivery_info: Optional[str] = None
    notes: Optional[str] = None
    idempotency_key: Optional[str] = None  # 幂等性键（防止重复提交，建议客户端生成UUID）


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

    # 获取所有商品的ID
    product_ids = [p.id for p in products]

    # 批量查询SKU库存信息（用于SKU商品的库存判断）
    sku_stock_result = await db.execute(
        select(
            PointProductSKU.product_id,
            func.sum(PointProductSKU.stock).label('total_stock'),
        ).where(
            PointProductSKU.product_id.in_(product_ids),
            PointProductSKU.is_active == True
        ).group_by(PointProductSKU.product_id)
    )
    sku_stock_map = {row.product_id: row.total_stock for row in sku_stock_result.fetchall()}

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
        # 检查库存：过滤掉无库存的商品
        if p.has_sku:
            # SKU商品：检查是否有SKU库存
            total_sku_stock = sku_stock_map.get(p.id, 0) or 0
            if total_sku_stock <= 0:
                continue  # 跳过无库存的SKU商品
            stock = total_sku_stock
            stock_unlimited = False
        else:
            # 非SKU商品：检查商品库存
            if not p.stock_unlimited and p.stock <= 0:
                continue  # 跳过无库存的商品
            stock = p.stock
            stock_unlimited = p.stock_unlimited

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
            "stock": stock if not stock_unlimited else 999,
            "stock_unlimited": stock_unlimited,
            "category": category_name,
            "has_sku": p.has_sku,
            "sold": p.sold or 0,
            "total_sold": (p.sold or 0) + (p.fake_sold or 0),  # 总销量 = 实际销量 + 注水销量
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
        "sold": product.sold or 0,
        "fake_sold": product.fake_sold or 0,
        "total_sold": (product.sold or 0) + (product.fake_sold or 0),  # 总销量
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


class ShippingCostRequest(BaseModel):
    """运费计算请求"""
    product_id: str = Field(..., description="商品ID")
    address_id: str = Field(..., description="收货地址ID")
    sku_id: Optional[str] = Field(None, description="SKU ID（多规格商品时需要）")
    quantity: int = Field(1, ge=1, description="购买数量")


class ShippingCostResponse(BaseModel):
    """运费计算响应"""
    deliverable: bool = Field(..., description="是否可配送")
    shipping_cost: int = Field(..., description="运费（分）")
    free_shipping: bool = Field(..., description="是否包邮")
    free_shipping_reason: Optional[str] = Field(None, description="包邮原因")
    reason: Optional[str] = Field(None, description="不可配送原因")
    region_name: Optional[str] = Field(None, description="区域名称")
    estimate_days_min: Optional[int] = Field(None, description="预计最少天数")
    estimate_days_max: Optional[int] = Field(None, description="预计最多天数")


@router.post("/shipping-cost", response_model=ShippingCostResponse)
async def calculate_shipping_cost(
    body: ShippingCostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """计算运费

    根据商品、收货地址和数量计算运费
    """
    from app.models.point_product import PointProduct
    from app.models.address import UserAddress
    from app.services.shipping_service import ShippingTemplateService

    # 1. 查询商品信息
    result = await db.execute(
        select(PointProduct).where(PointProduct.id == body.product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException("商品不存在", code="PRODUCT_NOT_FOUND")

    # 2. 检查是否需要运费（虚拟商品或无需快递的商品）
    if product.product_type == "virtual" or product.shipping_method == "no_shipping":
        return ShippingCostResponse(
            deliverable=True,
            shipping_cost=0,
            free_shipping=True,
            free_shipping_reason="no_shipping_needed",
        )

    # 3. 如果没有运费模板，默认免运费
    if not product.shipping_template_id:
        return ShippingCostResponse(
            deliverable=True,
            shipping_cost=0,
            free_shipping=True,
            free_shipping_reason="no_template",
        )

    # 4. 查询收货地址
    result = await db.execute(
        select(UserAddress).where(UserAddress.id == body.address_id)
    )
    address = result.scalar_one_or_none()
    if not address:
        raise NotFoundException("地址不存在", code="ADDRESS_NOT_FOUND")

    # 5. 计算运费
    service = ShippingTemplateService(db)
    cost_result = await service.calculate_shipping_cost(
        template_id=str(product.shipping_template_id),
        region_code=address.province_code,
        quantity=body.quantity,
    )

    return ShippingCostResponse(
        deliverable=cost_result.get("deliverable", True),
        shipping_cost=cost_result.get("shipping_cost", 0),
        free_shipping=cost_result.get("free_shipping", False),
        free_shipping_reason=cost_result.get("free_shipping_reason"),
        reason=cost_result.get("reason"),
        region_name=cost_result.get("region_name"),
        estimate_days_min=cost_result.get("estimate_days_min"),
        estimate_days_max=cost_result.get("estimate_days_max"),
    )


@router.post("/orders")
async def create_user_order(
    body: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_point_order),  # 请求频率限制：5次/分钟
):
    """下单

    支持以下保护机制：
    - 请求频率限制：5次/分钟
    - 幂等性检查：防止重复提交（60秒内）
    - 分布式锁：防止并发下单
    - 行级锁：库存安全扣减
    """
    from app.models.point_product import PointProduct
    from app.models.point_sku import PointProductSKU
    from app.models.address import UserAddress
    from app.services.ability_points_service import get_or_create_user_points
    from app.services.shipping_service import ShippingTemplateService

    # 生成幂等性键和锁键
    idempotency_key = body.idempotency_key or f"order:{current_user.id}:{body.product_id}:{body.sku_id or 'default'}"
    lock_key = f"order:{current_user.id}:{body.product_id}"

    # 使用组合锁（幂等性检查 + 分布式锁）
    async with CombinedLock(
        idempotency_key=idempotency_key,
        lock_key=lock_key,
        idempotency_ttl=60,
        lock_timeout=30,
    ) as combined_lock:
        # 幂等性检查
        if combined_lock.is_duplicate:
            raise BusinessException(
                "订单正在处理中，请勿重复提交",
                code="DUPLICATE_REQUEST"
            )

        # 分布式锁检查
        if not combined_lock.lock_acquired:
            raise BusinessException(
                "订单正在处理中，请稍后再试",
                code="ORDER_PROCESSING"
            )

        # 1. 查询商品信息（加行级锁）
        from app.models.point_product import PointProduct
        result = await db.execute(
            select(PointProduct)
            .where(PointProduct.id == body.product_id)
            .with_for_update()
        )
        product = result.scalar_one_or_none()
        if not product:
            raise NotFoundException("商品不存在", code="PRODUCT_NOT_FOUND")
        if not product.is_active:
            raise BusinessException("商品已下架", code="PRODUCT_INACTIVE")

        # 2. 确定积分价格和库存检查
        points_cost = product.points_cost
        sku = None
        if body.sku_id:
            # SKU商品：查询SKU信息（加行级锁）
            result = await db.execute(
                select(PointProductSKU)
                .where(PointProductSKU.id == body.sku_id)
                .with_for_update()
            )
            sku = result.scalar_one_or_none()
            if not sku:
                raise NotFoundException("SKU不存在", code="SKU_NOT_FOUND")
            if not sku.is_active:
                raise BusinessException("SKU已下架", code="SKU_INACTIVE")
            if not sku.stock_unlimited and sku.stock <= 0:
                raise BusinessException("SKU库存不足", code="INSUFFICIENT_STOCK")
            points_cost = sku.points_cost
        else:
            # 非SKU商品：检查商品库存
            if not product.stock_unlimited and product.stock <= 0:
                raise BusinessException("商品库存不足", code="INSUFFICIENT_STOCK")

        # 3. 检查积分是否足够
        user_points_record = await get_or_create_user_points(db, current_user.id)
        user_points = user_points_record.available_points
        if user_points < points_cost:
            raise BusinessException(
                f"积分不足，当前积分{user_points}，需要{points_cost}积分",
                code="INSUFFICIENT_POINTS"
            )

        # 4. 配送区域校验
        # 判断是否需要收货地址：
        # - 只有虚拟商品不需要地址
        # - 实物商品和套餐商品需要快递或自提时，需要地址
        need_address = (
            product.product_type != 'virtual' and
            product.shipping_method != 'no_shipping'
        )

        if need_address:
            if not body.address_id:
                raise BusinessException("请选择收货地址", code="ADDRESS_REQUIRED")

            # 查询地址
            result = await db.execute(
                select(UserAddress).where(UserAddress.id == body.address_id)
            )
            address = result.scalar_one_or_none()
            if not address:
                raise NotFoundException("地址不存在", code="ADDRESS_NOT_FOUND")

            # 检查配送区域
            if product.shipping_template_id:
                service = ShippingTemplateService(db)
                template = await service.get_template(str(product.shipping_template_id))
                if template:
                    province = address.province_name

                    # 检查不配送区域
                    regions = await service.list_regions(str(product.shipping_template_id))
                    excluded_region_names = []
                    for region in regions:
                        if region.no_delivery:
                            excluded_region_names.append(region.region_name)

                    if excluded_region_names:
                        is_excluded = any(
                            name in province or province in name
                            for name in excluded_region_names
                        )
                        if is_excluded:
                            raise BusinessException(
                                f"该地址不在配送范围内（{province}）",
                                code="DELIVERY_NOT_AVAILABLE"
                            )

        # 5. 创建订单（在事务中完成库存扣减和积分扣除）
        order = await create_order(
            db,
            current_user.id,
            body.product_id,
            body.delivery_info,
            body.notes,
            body.address_id,
            body.sku_id,
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
    category_id: Optional[str] = Query(None, description="分类ID筛选"),
    product_type: Optional[str] = Query(None, description="商品类型筛选: virtual/physical/bundle"),
    is_active: Optional[bool] = Query(None, description="上架状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（商品名称）"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有商品（管理员）- 支持筛选"""
    from app.models.point_category import PointCategory
    from app.models.point_product import PointProduct
    from app.models.point_sku import PointProductSKU
    from sqlalchemy import func
    from sqlalchemy.orm import joinedload

    # 构建查询
    query = select(PointProduct)

    # 应用筛选条件
    if active_only:
        query = query.where(PointProduct.is_active == True)
    if is_active is not None:
        query = query.where(PointProduct.is_active == is_active)
    if category_id:
        query = query.where(PointProduct.category_id == category_id)
    if product_type:
        query = query.where(PointProduct.product_type == product_type)
    if keyword:
        query = query.where(PointProduct.name.contains(keyword))

    # 按排序权重和创建时间排序
    query = query.order_by(PointProduct.sort_order.desc(), PointProduct.created_at.desc())

    result = await db.execute(query)
    products = result.scalars().all()

    # 批量查询所有需要的分类
    category_ids = [p.category_id for p in products if p.category_id]
    category_map = {}
    if category_ids:
        result = await db.execute(
            select(PointCategory).where(PointCategory.id.in_(category_ids))
        )
        for cat in result.scalars().all():
            category_map[str(cat.id)] = cat.name

    # 批量查询所有SKU商品的库存和销量汇总
    product_ids = [p.id for p in products if p.has_sku]
    sku_aggregates = {}
    if product_ids:
        result = await db.execute(
            select(
                PointProductSKU.product_id,
                func.sum(PointProductSKU.stock).label('total_stock'),
                func.sum(PointProductSKU.sold).label('total_sold'),
                func.sum(func.coalesce(PointProductSKU.stock_unlimited, False)).label('any_unlimited')
            ).where(
                PointProductSKU.product_id.in_(product_ids)
            ).group_by(PointProductSKU.product_id)
        )
        for row in result.all():
            sku_aggregates[row.product_id] = {
                'stock': row.total_stock or 0,
                'sold': row.total_sold or 0,
                'stock_unlimited': row.any_unlimited > 0
            }

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

        # 获取库存和销量（SKU商品从SKU汇总，否则从商品本身）
        if p.has_sku and p.id in sku_aggregates:
            stock = sku_aggregates[p.id]['stock']
            sold = sku_aggregates[p.id]['sold']
            stock_unlimited = sku_aggregates[p.id]['stock_unlimited']
        else:
            stock = p.stock
            sold = p.sold or 0
            stock_unlimited = p.stock_unlimited

        # 总销量 = 实际销量 + 注水销量
        total_sold = sold + (p.fake_sold or 0)

        data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "image_urls": image_urls,
            "image_url": image_urls[0] if image_urls else None,  # 兼容旧版
            "points_cost": p.points_cost,
            "stock": stock,
            "stock_unlimited": stock_unlimited,
            "sold": sold,
            "fake_sold": p.fake_sold or 0,
            "total_sold": total_sold,
            "category": category_name,
            "category_id": str(p.category_id) if p.category_id else None,
            "has_sku": p.has_sku,
            "product_type": p.product_type,
            "shipping_method": p.shipping_method,
            "shipping_template_id": str(p.shipping_template_id) if p.shipping_template_id else None,
            "is_active": p.is_active,
            "off_shelf_reason": p.off_shelf_reason,
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
        fake_sold=body.fake_sold,
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

            # 生成SKU编码 - 始终使用产品ID前缀确保全局唯一
            # 格式: SKU-{product_id前8位}-{序号}
            sku_code = f"SKU-{product.id[:8]}-{idx+1}"

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
    # 获取排除SKU相关字段的更新数据
    update_data = body.model_dump(exclude_unset=True, exclude={'specifications', 'skus'})
    await update_product(db, product_id, **update_data)

    # 处理SKU同步
    if body.has_sku and body.specifications is not None and body.skus is not None:
        # 1. 删除旧的规格和SKU
        # 先删除SKU
        await db.execute(
            delete(PointProductSKU).where(PointProductSKU.product_id == product_id)
        )
        # 再删除规格值
        spec_ids_result = await db.execute(
            select(PointSpecification.id).where(PointSpecification.product_id == product_id)
        )
        spec_ids = [row[0] for row in spec_ids_result.fetchall()]
        if spec_ids:
            await db.execute(
                delete(PointSpecificationValue).where(PointSpecificationValue.specification_id.in_(spec_ids))
            )
        # 最后删除规格
        await db.execute(
            delete(PointSpecification).where(PointSpecification.product_id == product_id)
        )

        # 2. 创建新的规格和SKU
        spec_id_map = {}  # 规格名 -> 规格ID

        for spec_data in body.specifications:
            spec_name = spec_data.name
            spec_values = spec_data.values

            if not spec_name:
                continue

            # 创建规格
            spec = PointSpecification(
                product_id=product_id,
                name=spec_name,
                sort_order=0,
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

        # 创建SKU
        for idx, sku_data in enumerate(body.skus):
            specs_dict = sku_data.specs
            if not specs_dict:
                continue

            # 生成SKU编码 - 始终使用产品ID前缀确保全局唯一
            # 格式: SKU-{product_id前8位}-{序号}
            sku_code = f"SKU-{product_id[:8]}-{idx+1}"

            # 创建SKU
            sku = PointProductSKU(
                product_id=product_id,
                sku_code=sku_code,
                specs=json.dumps(specs_dict, ensure_ascii=False),
                points_cost=sku_data.points_cost or body.points_cost or 0,
                stock=sku_data.stock,
                stock_unlimited=sku_data.stock_unlimited,
                image_url=sku_data.image_url,
                sort_order=sku_data.sort_order or idx,
                is_active=sku_data.is_active,
            )
            db.add(sku)

        await db.commit()

    return success_response(message="商品更新成功")


@router.delete("/admin/products/{product_id}")
async def admin_delete_product(
    product_id: str,
    body: Optional[OffShelfRequest] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除商品（管理员，软删除）"""
    # 更新下架原因
    if body and body.reason:
        from app.models.point_product import PointProduct as ProductModel
        result = await db.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        product = result.scalar_one_or_none()
        if product:
            product.off_shelf_reason = body.reason
            await db.commit()

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
    from sqlalchemy.orm import joinedload

    # 构建查询，关联加载商品信息
    query = select(PointOrder).options(joinedload(PointOrder.product))

    if status:
        query = query.where(PointOrder.status == status)

    query = query.order_by(PointOrder.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    orders = result.scalars().unique().all()

    data = []
    for o in orders:
        # 获取商品的发货相关信息
        product = o.product
        product_type = product.product_type if product else None
        shipping_method = product.shipping_method if product else None

        data.append({
            "id": o.id,
            "order_number": o.order_number,
            "user_id": o.user_id,
            "product_name": o.product_name,
            "points_cost": o.points_cost,
            "status": o.status,
            "product_type": product_type,
            "shipping_method": shipping_method,
            "shipment_id": str(o.shipment_id) if o.shipment_id else None,
            "created_at": o.created_at.isoformat(),
            "processed_at": o.processed_at.isoformat() if o.processed_at else None,
        })

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
