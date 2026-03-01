"""积分商品API - Sprint 4.7 商品兑换系统"""
import json
from typing import Dict, List, Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user, get_current_user, rate_limit_point_order
from app.core.exceptions import BusinessException, NotFoundException, success_response
from app.models.address import UserAddress
from app.models.point_order import PointOrder
from app.models.point_sku import PointProductSKU, PointSpecification, PointSpecificationValue
from app.models.user import User
from app.schemas.point_product import PointProductUpdate as ProductUpdate
from app.services.point_product_service import (cancel_order, create_order, calculate_order_price,  # 商品管理; 订单管理
                                                create_product, delete_product, get_order,
                                                get_product, list_all_orders, list_my_orders,
                                                list_products, process_order, update_product)
from app.utils.distributed_lock import CombinedLock
from app.utils.client_ip import get_client_ip
from fastapi import APIRouter, Body, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import Integer, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import Literal

router = APIRouter(prefix="/point-shop", tags=["point-shop"])


# ============== Schemas ==============
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    points_cost: int = Field(..., gt=0)
    # 支付模式相关字段
    payment_mode: Literal["points_only", "cash_only", "mixed"] = Field("points_only", description="支付模式")
    cash_price: Optional[int] = Field(None, ge=0, description="现金价格（分）- 纯现金模式")
    mixed_points_cost: Optional[int] = Field(None, ge=0, description="混合支付时的积分价格")
    mixed_cash_price: Optional[int] = Field(None, ge=0, description="混合支付时的现金价格（分）")
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
    # 支付模式相关字段
    payment_mode: Optional[Literal["points_only", "cash_only", "mixed"]] = Field(None, description="支付模式")
    cash_price: Optional[int] = Field(None, ge=0, description="现金价格（分）")
    mixed_points_cost: Optional[int] = Field(None, ge=0, description="混合支付时的积分价格")
    mixed_cash_price: Optional[int] = Field(None, ge=0, description="混合支付时的现金价格（分）")
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
    # SKU相关数据
    specifications: Optional[List[dict]] = Field(None, description="规格列表")
    skus: Optional[List[dict]] = Field(None, description="SKU列表")


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
    # 同时检查是否有无限库存的SKU
    sku_stock_result = await db.execute(
        select(
            PointProductSKU.product_id,
            func.sum(PointProductSKU.stock).label('total_stock'),
            func.sum(func.coalesce(PointProductSKU.stock_unlimited, False).cast(Integer)).label('has_unlimited'),
        ).where(
            PointProductSKU.product_id.in_(product_ids),
            PointProductSKU.is_active == True
        ).group_by(PointProductSKU.product_id)
    )
    sku_stock_map = {}
    for row in sku_stock_result.fetchall():
        sku_stock_map[row.product_id] = {
            'total_stock': row.total_stock or 0,
            'has_unlimited': row.has_unlimited > 0
        }

    # 批量查询SKU商品的第一个SKU价格信息（用于多规格商品的价格显示）
    # 使用子查询获取每个商品的最小SKU ID
    first_sku_result = await db.execute(
        select(PointProductSKU).where(
            PointProductSKU.id.in_(
                select(func.min(PointProductSKU.id)).where(
                    PointProductSKU.product_id.in_(product_ids),
                    PointProductSKU.is_active == True
                ).group_by(PointProductSKU.product_id)
            )
        )
    )
    first_sku_map = {}
    for sku in first_sku_result.scalars().all():
        first_sku_map[sku.product_id] = sku

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
            # SKU商品：检查是否有SKU库存或无限库存
            sku_info = sku_stock_map.get(p.id, {'total_stock': 0, 'has_unlimited': False})
            has_unlimited = sku_info['has_unlimited']
            total_stock = sku_info['total_stock']
            if not has_unlimited and total_stock <= 0:
                continue  # 跳过无库存的SKU商品
            stock = total_stock
            stock_unlimited = has_unlimited
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

        # 对于多规格商品，使用第一个SKU的价格
        first_sku = first_sku_map.get(p.id) if p.has_sku else None
        if first_sku:
            points_cost = first_sku.points_cost or p.points_cost
            cash_price = first_sku.cash_price if first_sku.cash_price is not None else p.cash_price
            mixed_points_cost = first_sku.mixed_points_cost if first_sku.mixed_points_cost is not None else p.mixed_points_cost
            mixed_cash_price = first_sku.mixed_cash_price if first_sku.mixed_cash_price is not None else p.mixed_cash_price
        else:
            points_cost = p.points_cost
            cash_price = p.cash_price
            mixed_points_cost = p.mixed_points_cost
            mixed_cash_price = p.mixed_cash_price

        data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "image_urls": image_urls,
            "image_url": image_urls[0] if image_urls else None,  # 兼容旧版
            "points_cost": points_cost,
            # 支付模式相关字段
            "payment_mode": p.payment_mode or "points_only",
            "cash_price": cash_price,
            "mixed_points_cost": mixed_points_cost,
            "mixed_cash_price": mixed_cash_price,
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
        # 支付模式相关字段
        "payment_mode": product.payment_mode or "points_only",
        "cash_price": product.cash_price,
        "mixed_points_cost": product.mixed_points_cost,
        "mixed_cash_price": product.mixed_cash_price,
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
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_point_order),  # 请求频率限制：5次/分钟
):
    """下单 - 支持混合支付

    支持以下保护机制：
    - 请求频率限制：5次/分钟
    - 幂等性检查：防止重复提交（60秒内）
    - 分布式锁：防止并发下单
    - 行级锁：库存安全扣减

    返回字段：
    - need_payment: 是否需要支付（纯积分时为false）
    - payment_id: 支付ID（需要支付时返回）
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

        # 2. 确定SKU和价格
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
        else:
            # 非SKU商品：检查商品库存
            if not product.stock_unlimited and product.stock <= 0:
                raise BusinessException("商品库存不足", code="INSUFFICIENT_STOCK")

        # 3. 计算订单价格（根据支付模式）
        price_info = calculate_order_price(product, sku)
        points_cost = price_info["points_cost"]
        cash_amount = price_info["cash_amount"] or 0

        # 3.5 计算运费（如果需要配送）
        shipping_cost = 0
        need_address = (
            product.product_type != 'virtual' and
            product.shipping_method != 'no_shipping'
        )
        if need_address and product.shipping_template_id and body.address_id:
            # 查询地址
            result = await db.execute(
                select(UserAddress).where(UserAddress.id == body.address_id)
            )
            address = result.scalar_one_or_none()
            if address:
                # 计算运费
                shipping_service = ShippingTemplateService(db)
                shipping_result = await shipping_service.calculate_shipping_cost(
                    template_id=str(product.shipping_template_id),
                    region_code=address.province_code,
                    quantity=1,
                )
                if shipping_result.get("deliverable", True) and not shipping_result.get("free_shipping", False):
                    shipping_cost = shipping_result.get("shipping_cost", 0)

        # 将运费加到现金价格中
        if shipping_cost > 0:
            cash_amount = cash_amount + shipping_cost
            price_info["cash_amount"] = cash_amount
            price_info["shipping_cost"] = shipping_cost
            if cash_amount > 0:
                price_info["need_payment"] = True

        # 4. 检查积分是否足够（如果需要积分）
        if points_cost > 0:
            user_points_record = await get_or_create_user_points(db, current_user.id)
            user_points = user_points_record.available_points
            if user_points < points_cost:
                raise BusinessException(
                    f"积分不足，当前积分{user_points}，需要{points_cost}积分",
                    code="INSUFFICIENT_POINTS"
                )

        # 5. 配送区域校验
        if need_address:
            if not body.address_id:
                raise BusinessException("请选择收货地址", code="ADDRESS_REQUIRED")

            # 查询地址
            addr_result = await db.execute(
                select(UserAddress).where(UserAddress.id == body.address_id)
            )
            address = addr_result.scalar_one_or_none()
            if not address:
                raise NotFoundException("地址不存在", code="ADDRESS_NOT_FOUND")

            if product.shipping_template_id:
                service = ShippingTemplateService(db)
                template = await service.get_template(str(product.shipping_template_id))
                if template:
                    province = address.province_name
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

        # 6. 创建订单（在事务中完成库存扣减）
        order, order_price_info = await create_order(
            db,
            current_user.id,
            body.product_id,
            body.delivery_info,
            body.notes,
            body.address_id,
            body.sku_id,
            shipping_cost=shipping_cost,  # 传入运费
        )

        need_payment = order_price_info["need_payment"]
        order_shipping_cost = order_price_info.get("shipping_cost", 0)

        data = {
            "id": order.id,
            "order_number": order.order_number,
            "product_name": order.product_name,
            "payment_mode": order.payment_mode,
            "points_cost": order.points_cost,
            "cash_amount": order.cash_amount,
            "shipping_cost": order_shipping_cost,  # 运费
            "need_payment": need_payment,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
        }

        # 7. 如果需要支付，创建支付流水
        if need_payment:
            from app.services.point_payment_service import create_point_payment
            client_ip = get_client_ip(request)

            try:
                payment, payment_params = await create_point_payment(
                    db,
                    order.id,
                    current_user.id,
                    current_user.openid,
                    client_ip,
                    idempotency_key=f"payment:{order.id}",
                )
                data["payment_id"] = payment.id
                data["payment_params"] = payment_params
            except BusinessException as e:
                # 业务异常（如重复支付、状态不正确等），向上传递让前端处理
                raise e
            except Exception as e:
                # 其他异常（如微信支付接口调用失败），记录日志但订单仍然有效
                # 用户可以稍后在订单详情页重试支付
                import logging
                logging.getLogger(__name__).error(f"Failed to create payment for order {order.id}: {e}")
                # 不设置 payment_params，前端会提示用户稍后重试支付

        message = "下单成功" if not need_payment else "下单成功，请完成支付"
        return success_response(data=data, message=message)


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
        "payment_mode": o.payment_mode or "points_only",
        "cash_amount": o.cash_amount,
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
        "payment_mode": order.payment_mode or "points_only",
        "points_cost": order.points_cost,
        "cash_amount": order.cash_amount,
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
            # 支付模式相关字段
            "payment_mode": p.payment_mode or "points_only",
            "cash_price": p.cash_price,
            "mixed_points_cost": p.mixed_points_cost,
            "mixed_cash_price": p.mixed_cash_price,
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
        payment_mode=body.payment_mode,
        cash_price=body.cash_price,
        mixed_points_cost=body.mixed_points_cost,
        mixed_cash_price=body.mixed_cash_price,
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
                # 支付价格字段
                cash_price=sku_data.get("cash_price"),
                mixed_points_cost=sku_data.get("mixed_points_cost"),
                mixed_cash_price=sku_data.get("mixed_cash_price"),
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
        # 支付模式相关字段
        "payment_mode": product.payment_mode or "points_only",
        "cash_price": product.cash_price,
        "mixed_points_cost": product.mixed_points_cost,
        "mixed_cash_price": product.mixed_cash_price,
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
        "fake_sold": product.fake_sold or 0,
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
            spec_name = spec_data.get('name') if isinstance(spec_data, dict) else spec_data.name
            spec_values = spec_data.get('values', []) if isinstance(spec_data, dict) else spec_data.values

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
            specs_dict = sku_data.get('specs') if isinstance(sku_data, dict) else sku_data.specs
            if not specs_dict:
                continue

            # 生成SKU编码 - 始终使用产品ID前缀确保全局唯一
            # 格式: SKU-{product_id前8位}-{序号}
            sku_code = f"SKU-{product_id[:8]}-{idx+1}"

            # 获取SKU数据中的支付价格字段
            sku_dict = sku_data if isinstance(sku_data, dict) else sku_data.model_dump()

            # 创建SKU
            sku = PointProductSKU(
                product_id=product_id,
                sku_code=sku_code,
                specs=json.dumps(specs_dict, ensure_ascii=False),
                points_cost=sku_dict.get('points_cost') or body.points_cost or 0,
                stock=sku_dict.get('stock'),
                stock_unlimited=sku_dict.get('stock_unlimited'),
                image_url=sku_dict.get('image_url'),
                sort_order=sku_dict.get('sort_order') or idx,
                is_active=sku_dict.get('is_active', True),
                # 支付价格字段
                cash_price=sku_dict.get("cash_price"),
                mixed_points_cost=sku_dict.get("mixed_points_cost"),
                mixed_cash_price=sku_dict.get("mixed_cash_price"),
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

    # 批量查询所有需要的地址
    address_ids = [o.address_id for o in orders if o.address_id]
    address_map = {}
    if address_ids:
        addr_result = await db.execute(
            select(UserAddress).where(UserAddress.id.in_(address_ids))
        )
        for addr in addr_result.scalars().all():
            address_map[str(addr.id)] = addr

    data = []
    for o in orders:
        # 获取商品的发货相关信息
        product = o.product
        product_type = product.product_type if product else None
        shipping_method = product.shipping_method if product else None

        # 获取收货地址信息
        address = None
        if o.address_id and str(o.address_id) in address_map:
            addr = address_map[str(o.address_id)]
            address = {
                "id": str(addr.id),
                "contact_name": addr.contact_name,
                "contact_phone": addr.contact_phone,
                "province_name": addr.province_name,
                "city_name": addr.city_name,
                "district_name": addr.district_name,
                "detailed_address": addr.detailed_address,
                "full_address": f"{addr.province_name or ''}{addr.city_name or ''}{addr.district_name or ''}{addr.detailed_address or ''}",
            }

        data.append({
            "id": o.id,
            "order_number": o.order_number,
            "user_id": o.user_id,
            "product_name": o.product_name,
            "payment_mode": o.payment_mode or "points_only",
            "points_cost": o.points_cost,
            "cash_amount": o.cash_amount,
            "status": o.status,
            "product_type": product_type,
            "shipping_method": shipping_method,
            "shipment_id": str(o.shipment_id) if o.shipment_id else None,
            "address": address,
            "delivery_info": o.delivery_info,
            "notes": o.notes,
            "created_at": o.created_at.isoformat(),
            "processed_at": o.processed_at.isoformat() if o.processed_at else None,
        })

    return success_response(data={"orders": data, "total": len(data)})


@router.get("/admin/orders/{order_id}")
async def admin_get_order_detail(
    order_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取订单详情（管理员）"""
    from sqlalchemy.orm import joinedload

    # 查询订单
    result = await db.execute(
        select(PointOrder)
        .options(joinedload(PointOrder.product))
        .where(PointOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundException("订单不存在", code="ORDER_NOT_FOUND")

    # 查询收货地址
    address = None
    if order.address_id:
        addr_result = await db.execute(
            select(UserAddress).where(UserAddress.id == order.address_id)
        )
        addr = addr_result.scalar_one_or_none()
        if addr:
            address = {
                "id": str(addr.id),
                "contact_name": addr.contact_name,
                "contact_phone": addr.contact_phone,
                "province_name": addr.province_name,
                "city_name": addr.city_name,
                "district_name": addr.district_name,
                "detailed_address": addr.detailed_address,
                "full_address": f"{addr.province_name or ''}{addr.city_name or ''}{addr.district_name or ''}{addr.detailed_address or ''}",
            }

    # 查询发货信息
    shipment = None
    if order.shipment_id:
        from app.models.point_shipment import PointShipment
        ship_result = await db.execute(
            select(PointShipment).where(PointShipment.id == order.shipment_id)
        )
        ship = ship_result.scalar_one_or_none()
        if ship:
            shipment = {
                "id": str(ship.id),
                "courier_code": ship.courier_code,
                "courier_name": ship.courier_name,
                "tracking_number": ship.tracking_number,
                "status": ship.status,
                "shipped_at": ship.shipped_at.isoformat() if ship.shipped_at else None,
                "delivered_at": ship.delivered_at.isoformat() if ship.delivered_at else None,
            }

    # 获取商品信息
    product = order.product
    product_type = product.product_type if product else None
    shipping_method = product.shipping_method if product else None

    data = {
        "id": order.id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "product_id": str(order.product_id) if order.product_id else None,
        "product_name": order.product_name,
        "product_image": order.product_image,
        "payment_mode": order.payment_mode or "points_only",
        "points_cost": order.points_cost,
        "cash_amount": order.cash_amount,
        "payment_status": order.payment_status,
        "points_deducted": order.points_deducted,
        "status": order.status,
        "product_type": product_type,
        "shipping_method": shipping_method,
        "address": address,
        "shipment": shipment,
        "shipment_id": str(order.shipment_id) if order.shipment_id else None,
        "delivery_info": order.delivery_info,
        "notes": order.notes,
        "notes_admin": order.notes_admin,
        "transaction_id": order.transaction_id,
        "created_at": order.created_at.isoformat(),
        "processed_at": order.processed_at.isoformat() if order.processed_at else None,
    }

    return success_response(data=data)


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


# ============== 支付相关接口 ==============

class CreatePaymentRequest(BaseModel):
    """创建支付请求"""
    order_id: str = Field(..., description="订单ID")
    idempotency_key: Optional[str] = Field(None, description="幂等性键")


@router.post("/payments/create")
async def create_payment(
    body: CreatePaymentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建支付

    为需要现金支付的订单创建微信支付
    """
    from app.services.point_payment_service import create_point_payment

    client_ip = get_client_ip(request)

    payment, payment_params = await create_point_payment(
        db,
        body.order_id,
        current_user.id,
        current_user.openid,
        client_ip,
        idempotency_key=body.idempotency_key,
    )

    return success_response(data={
        "payment_id": payment.id,
        "out_trade_no": payment.out_trade_no,
        "cash_amount": payment.cash_amount,
        "points_amount": payment.points_amount,
        "payment_params": payment_params,
    })


@router.get("/payments/{payment_id}")
async def get_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询支付状态"""
    from app.services.point_payment_service import query_payment_status

    payment = await query_payment_status(db, payment_id, current_user.id)
    if not payment:
        raise NotFoundException("支付记录不存在", code="PAYMENT_NOT_FOUND")

    return success_response(data={
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "out_trade_no": payment.out_trade_no,
        "status": payment.status,
        "cash_amount": payment.cash_amount,
        "points_amount": payment.points_amount,
        "payment_method": payment.payment_method,
        "transaction_id": payment.transaction_id,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        "fail_code": payment.fail_code,
        "fail_message": payment.fail_message,
        "created_at": payment.created_at.isoformat(),
    })


@router.post("/payments/notify/wechat")
async def wechat_payment_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """微信支付回调通知

    注意：此接口不需要认证，由微信服务器调用
    """
    from app.utils.wechat_pay import parse_payment_notify
    from app.services.point_payment_service import (
        handle_point_payment_notify,
        generate_payment_response,
    )

    # 读取原始数据
    raw_body = await request.body()

    try:
        # 解析并验证签名
        notify_data = parse_payment_notify(raw_body)

        if not notify_data:
            return generate_payment_response("FAIL", "签名验证失败")

        # 处理回调
        success = await handle_point_payment_notify(db, notify_data)

        if success:
            return generate_payment_response("SUCCESS", "OK")
        else:
            return generate_payment_response("FAIL", "处理失败")

    except Exception as e:
        return generate_payment_response("FAIL", str(e))
