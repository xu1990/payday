"""积分商品服务 - Sprint 4.7 商品兑换系统"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.point_order import PointOrder
from app.models.point_product import PointProduct
from app.models.point_sku import PointProductSKU
from app.services.ability_points_service import add_points, spend_points
from app.utils.order_number import generate_order_number, is_order_number_exists
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession


def calculate_order_price(
    product: PointProduct,
    sku: Optional[PointProductSKU] = None,
) -> Dict:
    """
    计算订单价格

    返回:
    {
        "payment_mode": "points_only" | "cash_only" | "mixed",
        "points_cost": int,
        "cash_amount": int | None,
        "need_payment": bool
    }
    """
    payment_mode = product.payment_mode or "points_only"

    if payment_mode == "points_only":
        # 纯积分模式
        points_cost = sku.points_cost if sku and sku.points_cost else product.points_cost
        return {
            "payment_mode": "points_only",
            "points_cost": points_cost,
            "cash_amount": None,
            "need_payment": False
        }

    elif payment_mode == "cash_only":
        # 纯现金模式
        if sku and sku.cash_price is not None:
            cash_amount = sku.cash_price
        else:
            cash_amount = product.cash_price or 0
        return {
            "payment_mode": "cash_only",
            "points_cost": 0,
            "cash_amount": cash_amount,
            "need_payment": cash_amount > 0
        }

    elif payment_mode == "mixed":
        # 混合模式
        if sku:
            points_cost = sku.mixed_points_cost if sku.mixed_points_cost is not None else product.mixed_points_cost or 0
            cash_amount = sku.mixed_cash_price if sku.mixed_cash_price is not None else product.mixed_cash_price or 0
        else:
            points_cost = product.mixed_points_cost or 0
            cash_amount = product.mixed_cash_price or 0
        return {
            "payment_mode": "mixed",
            "points_cost": points_cost,
            "cash_amount": cash_amount,
            "need_payment": cash_amount > 0
        }

    # 默认返回纯积分
    return {
        "payment_mode": "points_only",
        "points_cost": product.points_cost,
        "cash_amount": None,
        "need_payment": False
    }

# ============== 商品管理（管理员） ==============

async def create_product(
    db: AsyncSession,
    name: str,
    points_cost: int,
    stock: int,
    stock_unlimited: bool = False,
    description: Optional[str] = None,
    image_urls: Optional[List[str]] = None,
    category: Optional[str] = None,
    sort_order: int = 0,
    *,
    has_sku: bool = False,
    product_type: str = "physical",
    shipping_method: str = "express",
    shipping_template_id: Optional[str] = None,
    category_id: Optional[str] = None,
    is_active: bool = True,
    fake_sold: int = 0,
    # 支付模式相关字段
    payment_mode: str = "points_only",
    cash_price: Optional[int] = None,
    mixed_points_cost: Optional[int] = None,
    mixed_cash_price: Optional[int] = None,
) -> PointProduct:
    """创建商品（管理员）"""
    if points_cost <= 0:
        raise ValidationException("积分价格必须大于0")

    if not stock_unlimited and stock < 0:
        raise ValidationException("库存不能为负数")

    # 将图片列表转换为JSON字符串
    image_urls_json = json.dumps(image_urls) if image_urls else None

    product = PointProduct(
        name=name,
        points_cost=points_cost,
        stock=stock,
        stock_unlimited=stock_unlimited,
        description=description,
        image_urls=image_urls_json,
        category=category,
        sort_order=sort_order,
        is_active=is_active,
        has_sku=has_sku,
        product_type=product_type,
        shipping_method=shipping_method,
        shipping_template_id=shipping_template_id,
        category_id=category_id,
        fake_sold=fake_sold,
        payment_mode=payment_mode,
        cash_price=cash_price,
        mixed_points_cost=mixed_points_cost,
        mixed_cash_price=mixed_cash_price,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession,
    product_id: str,
    **kwargs
) -> PointProduct:
    """更新商品（管理员）"""
    result = await db.execute(
        select(PointProduct).where(PointProduct.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundException("商品不存在")

    # 更新字段
    for key, value in kwargs.items():
        if hasattr(product, key) and value is not None:
            # 如果是image_urls参数，需要转换为JSON字符串
            if key == "image_urls" and isinstance(value, list):
                value = json.dumps(value)
            setattr(product, key, value)

    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: str) -> bool:
    """删除商品（软删除，设置is_active=False）"""
    result = await db.execute(
        select(PointProduct).where(PointProduct.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundException("商品不存在")

    product.is_active = False
    await db.commit()
    return True


async def list_products(
    db: AsyncSession,
    active_only: bool = True,
    category: Optional[str] = None,
) -> List[PointProduct]:
    """获取商品列表"""
    from app.models.point_category import PointCategory
    from sqlalchemy import or_

    query = select(PointProduct)

    if active_only:
        query = query.where(PointProduct.is_active == True)

    if category:
        # 尝试通过分类名称查找分类ID
        category_result = await db.execute(
            select(PointCategory.id).where(PointCategory.name == category).limit(1)
        )
        category_row = category_result.first()
        category_id = str(category_row[0]) if category_row else None

        # 同时匹配 category 名称或 category_id
        if category_id:
            query = query.where(
                or_(
                    PointProduct.category == category,
                    PointProduct.category_id == category_id
                )
            )
        else:
            query = query.where(PointProduct.category == category)

    query = query.order_by(
        PointProduct.sort_order.desc(),
        PointProduct.created_at.desc()
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: str) -> PointProduct:
    """获取商品详情"""
    result = await db.execute(
        select(PointProduct).where(PointProduct.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundException("商品不存在")

    return product


# ============== 订单管理 ==============

async def create_order(
    db: AsyncSession,
    user_id: str,
    product_id: str,
    delivery_info: Optional[str] = None,
    notes: Optional[str] = None,
    address_id: Optional[str] = None,
    sku_id: Optional[str] = None,
    shipping_cost: int = 0,  # 运费（分）
) -> Tuple[PointOrder, Dict]:
    """
    创建订单（用户下单）- 支持混合支付

    核心逻辑：
    1. 查询商品并锁定行
    2. 检查库存
    3. 计算订单价格（根据支付模式）
    4. 如果是纯积分模式：直接扣除积分
    5. 如果是混合模式：预检查积分余额（不扣除）
    6. 扣减库存、增加销量
    7. 创建订单

    返回: (订单对象, 价格信息字典)
    价格信息: {
        "payment_mode": str,
        "points_cost": int,
        "cash_amount": int | None,
        "need_payment": bool
    }

    并发安全：使用行级锁防止超卖
    """
    from app.models.point_sku import PointProductSKU

    # 1. 查询商品并加行级锁（防止并发问题）
    result = await db.execute(
        select(PointProduct)
        .where(PointProduct.id == product_id)
        .with_for_update()  # 行级锁
    )
    product = result.scalar_one_or_none()

    if not product:
        raise NotFoundException("商品不存在", code="PRODUCT_NOT_FOUND")

    if not product.is_active:
        raise BusinessException("商品已下架", code="PRODUCT_INACTIVE")

    # 如果指定了SKU，检查SKU库存
    sku = None
    if sku_id:
        result = await db.execute(
            select(PointProductSKU)
            .where(PointProductSKU.id == sku_id)
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
        # 2. 检查商品库存（非SKU商品）
        if not product.stock_unlimited and product.stock <= 0:
            raise BusinessException("商品库存不足", code="INSUFFICIENT_STOCK")

    # 3. 计算订单价格（根据支付模式）
    price_info = calculate_order_price(product, sku)
    payment_mode = price_info["payment_mode"]
    points_cost = price_info["points_cost"]
    cash_amount = price_info["cash_amount"] or 0
    need_payment = price_info["need_payment"]

    # 3.5 将运费加到现金价格中
    if shipping_cost > 0:
        cash_amount = cash_amount + shipping_cost
        price_info["cash_amount"] = cash_amount
        price_info["shipping_cost"] = shipping_cost
        if cash_amount > 0:
            need_payment = True
            price_info["need_payment"] = True

    # 4. 根据支付模式处理积分
    points_deducted = False
    if payment_mode == "points_only":
        # 纯积分模式：直接扣除积分
        await spend_points(
            db,
            user_id,
            points_cost,
            reference_id=product_id,
            reference_type="point_order",
            description=f"购买商品: {product.name}"
        )
        points_deducted = True
    elif payment_mode == "mixed":
        # 混合模式：锁定积分（防止支付等待期间被其他操作使用）
        from app.services.ability_points_service import lock_points
        await lock_points(
            db,
            user_id,
            points_cost,
            reference_id=product_id,
            reference_type="point_order",
            description=f"购买商品（锁定）: {product.name}"
        )
        # 注意：此时 points_deducted = False，等支付成功后再确认扣除

    # 5. 扣减库存、增加销量
    if sku:
        # SKU商品：扣减SKU库存和销量
        if not sku.stock_unlimited:
            sku.stock -= 1
        sku.sold = (sku.sold or 0) + 1
    else:
        # 非SKU商品：扣减商品库存和销量
        if not product.stock_unlimited:
            product.stock -= 1
        product.sold = (product.sold or 0) + 1

    # 6. 生成唯一订单号
    max_attempts = 10
    order_number = None
    for _ in range(max_attempts):
        order_number = generate_order_number()
        exists = await is_order_number_exists(db, order_number)
        if not exists:
            break
    else:
        raise BusinessException("生成订单号失败，请重试", code="ORDER_NUMBER_GENERATION_FAILED")

    # 7. 创建订单（保存第一张图片作为快照）
    first_image_url = None
    if product.image_urls:
        try:
            urls = json.loads(product.image_urls)
            if urls and len(urls) > 0:
                first_image_url = urls[0]
        except:
            pass

    # 根据支付模式设置订单支付状态和订单状态
    # 注意：如果有运费（shipping_cost > 0），即使是纯积分商品也需要支付现金
    if payment_mode == "points_only" and cash_amount == 0:
        # 纯积分模式且无运费：直接为已支付
        payment_status = "paid"
        order_status = "completed"
    else:
        # 需要现金支付（纯现金、混合模式、或纯积分+运费）
        payment_status = "unpaid"
        order_status = "pending"

    order = PointOrder(
        user_id=user_id,
        product_id=product_id,
        sku_id=sku_id,
        order_number=order_number,
        product_name=product.name,
        product_image=first_image_url,
        points_cost=points_cost,
        payment_mode=payment_mode,
        points_deducted=points_deducted,
        cash_amount=cash_amount,
        payment_status=payment_status,
        delivery_info=delivery_info,
        notes=notes,
        address_id=address_id,
        status=order_status,
    )
    db.add(order)

    await db.commit()
    await db.refresh(order)

    return order, price_info


async def list_my_orders(
    db: AsyncSession,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[PointOrder]:
    """获取我的订单列表"""
    query = select(PointOrder).where(PointOrder.user_id == user_id)

    if status:
        query = query.where(PointOrder.status == status)

    query = query.order_by(PointOrder.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_order(db: AsyncSession, order_id: str, user_id: str) -> PointOrder:
    """获取订单详情（用户）"""
    result = await db.execute(
        select(PointOrder).where(
            and_(PointOrder.id == order_id, PointOrder.user_id == user_id)
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundException("订单不存在")

    return order


async def cancel_order(
    db: AsyncSession,
    order_id: str,
    user_id: str
) -> PointOrder:
    """
    取消订单（用户）

    逻辑：
    1. 检查订单状态（只有pending可以取消）
    2. 退还/解锁积分（根据支付模式）
    3. 恢复库存、扣减销量
    4. 更新订单状态
    """
    from app.models.point_sku import PointProductSKU
    from app.services.ability_points_service import unlock_points

    result = await db.execute(
        select(PointOrder).where(
            and_(PointOrder.id == order_id, PointOrder.user_id == user_id)
        ).with_for_update()  # 行级锁
    )
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundException("订单不存在")

    if order.status != "pending":
        raise BusinessException("只有待处理订单可以取消", code="ORDER_CANNOT_CANCEL")

    # 根据支付模式处理积分退还
    if order.points_cost > 0:
        if order.payment_mode == "points_only" and order.points_deducted:
            # 纯积分模式且已扣除：退还积分
            await add_points(
                db,
                user_id,
                order.points_cost,
                event_type="order_cancelled",
                reference_id=order_id,
                reference_type="point_order",
                description=f"取消订单退款: {order.product_name}"
            )
        elif order.payment_mode == "mixed" and not order.points_deducted:
            # 混合模式且未确认扣除：解锁积分
            await unlock_points(
                db,
                user_id,
                order.points_cost,
                reference_id=order_id,
                reference_type="point_order",
                description=f"取消订单，解锁积分: {order.product_name}"
            )
            order.points_deducted = False  # 标记积分已解锁

    # 恢复库存、扣减销量
    if order.sku_id:
        # SKU订单：恢复SKU库存和销量
        sku_result = await db.execute(
            select(PointProductSKU)
            .where(PointProductSKU.id == order.sku_id)
            .with_for_update()
        )
        sku = sku_result.scalar_one_or_none()
        if sku:
            if not sku.stock_unlimited:
                sku.stock += 1
            sku.sold = max(0, (sku.sold or 0) - 1)
    else:
        # 非SKU订单：恢复商品库存和销量
        product_result = await db.execute(
            select(PointProduct)
            .where(PointProduct.id == order.product_id)
            .with_for_update()
        )
        product = product_result.scalar_one_or_none()
        if product:
            if not product.stock_unlimited:
                product.stock += 1
            product.sold = max(0, (product.sold or 0) - 1)

    # 更新订单状态
    order.status = "cancelled"

    await db.commit()
    await db.refresh(order)
    return order


# ============== 管理员订单管理 ==============

async def list_all_orders(
    db: AsyncSession,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[PointOrder]:
    """获取所有订单（管理员）"""
    query = select(PointOrder)

    if status:
        query = query.where(PointOrder.status == status)

    query = query.order_by(PointOrder.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def process_order(
    db: AsyncSession,
    order_id: str,
    admin_id: str,
    action: str,  # "complete" or "cancel"
    notes: Optional[str] = None,
) -> PointOrder:
    """
    处理订单（管理员）

    Args:
        action: "complete"（完成）或 "cancel"（取消/拒绝）
    """
    from app.models.point_sku import PointProductSKU
    from app.services.ability_points_service import unlock_points

    result = await db.execute(
        select(PointOrder).where(PointOrder.id == order_id).with_for_update()
    )
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundException("订单不存在")

    if order.status != "pending":
        raise BusinessException("只能处理待处理订单", code="ORDER_NOT_PENDING")

    if action == "complete":
        # 完成订单
        order.status = "completed"
        order.admin_id = admin_id
        order.processed_at = datetime.utcnow()
        order.notes_admin = notes
    elif action == "cancel":
        # 根据支付模式处理积分退还
        if order.points_cost > 0:
            if order.payment_mode == "points_only" and order.points_deducted:
                # 纯积分模式且已扣除：退还积分
                await add_points(
                    db,
                    order.user_id,
                    order.points_cost,
                    event_type="order_cancelled_by_admin",
                    reference_id=order_id,
                    reference_type="point_order",
                    description=f"订单被取消，退款: {order.product_name}"
                )
            elif order.payment_mode == "mixed" and not order.points_deducted:
                # 混合模式且未确认扣除：解锁积分
                await unlock_points(
                    db,
                    order.user_id,
                    order.points_cost,
                    reference_id=order_id,
                    reference_type="point_order",
                    description=f"管理员取消订单，解锁积分: {order.product_name}"
                )
                order.points_deducted = False  # 标记积分已解锁

        # 恢复库存、扣减销量
        if order.sku_id:
            # SKU订单：恢复SKU库存和销量
            sku_result = await db.execute(
                select(PointProductSKU)
                .where(PointProductSKU.id == order.sku_id)
                .with_for_update()
            )
            sku = sku_result.scalar_one_or_none()
            if sku:
                if not sku.stock_unlimited:
                    sku.stock += 1
                sku.sold = max(0, (sku.sold or 0) - 1)
        else:
            # 非SKU订单：恢复商品库存和销量
            product_result = await db.execute(
                select(PointProduct)
                .where(PointProduct.id == order.product_id)
                .with_for_update()
            )
            product = product_result.scalar_one_or_none()
            if product:
                if not product.stock_unlimited:
                    product.stock += 1
                product.sold = max(0, (product.sold or 0) - 1)

        order.status = "cancelled"
        order.admin_id = admin_id
        order.processed_at = datetime.utcnow()
        order.notes_admin = notes
    else:
        raise ValidationException("无效的操作", details={"action": action})

    await db.commit()
    await db.refresh(order)
    return order
