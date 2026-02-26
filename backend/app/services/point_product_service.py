"""积分商品服务 - Sprint 4.7 商品兑换系统"""
import json
from datetime import datetime
from typing import List, Optional

from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.point_order import PointOrder
from app.models.point_product import PointProduct
from app.services.ability_points_service import add_points, spend_points
from app.utils.order_number import generate_order_number, is_order_number_exists
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    query = select(PointProduct)

    if active_only:
        query = query.where(PointProduct.is_active == True)

    if category:
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
) -> PointOrder:
    """
    创建订单（用户下单）

    核心逻辑：
    1. 查询商品并锁定行
    2. 检查库存
    3. 扣除积分
    4. 扣减库存
    5. 创建订单

    并发安全：使用行级锁防止超卖
    """
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

    # 2. 检查库存
    if not product.stock_unlimited and product.stock <= 0:
        raise BusinessException("商品库存不足", code="INSUFFICIENT_STOCK")

    # 3. 扣除积分（会检查余额）
    await spend_points(
        db,
        user_id,
        product.points_cost,
        reference_id=product_id,
        reference_type="point_order",
        description=f"购买商品: {product.name}"
    )

    # 4. 扣减库存
    if not product.stock_unlimited:
        product.stock -= 1

    # 5. 生成唯一订单号
    max_attempts = 10
    order_number = None
    for _ in range(max_attempts):
        order_number = generate_order_number()
        exists = await is_order_number_exists(db, order_number)
        if not exists:
            break
    else:
        raise BusinessException("生成订单号失败，请重试", code="ORDER_NUMBER_GENERATION_FAILED")

    # 6. 创建订单（保存第一张图片作为快照）
    first_image_url = None
    if product.image_urls:
        try:
            urls = json.loads(product.image_urls)
            if urls and len(urls) > 0:
                first_image_url = urls[0]
        except:
            pass

    order = PointOrder(
        user_id=user_id,
        product_id=product_id,
        order_number=order_number,
        product_name=product.name,
        product_image=first_image_url,
        points_cost=product.points_cost,
        delivery_info=delivery_info,
        notes=notes,
        address_id=address_id,
        status="pending",
    )
    db.add(order)

    await db.commit()
    await db.refresh(order)

    return order


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
    2. 退还积分
    3. 恢复库存
    4. 更新订单状态
    """
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

    # 退还积分
    await add_points(
        db,
        user_id,
        order.points_cost,
        event_type="order_cancelled",
        reference_id=order_id,
        reference_type="point_order",
        description=f"取消订单退款: {order.product_name}"
    )

    # 恢复库存
    product_result = await db.execute(
        select(PointProduct)
        .where(PointProduct.id == order.product_id)
        .with_for_update()
    )
    product = product_result.scalar_one_or_none()
    if product and not product.stock_unlimited:
        product.stock += 1

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
        # 取消订单，退还积分
        await add_points(
            db,
            order.user_id,
            order.points_cost,
            event_type="order_cancelled_by_admin",
            reference_id=order_id,
            reference_type="point_order",
            description=f"订单被取消，退款: {order.product_name}"
        )

        # 恢复库存
        product_result = await db.execute(
            select(PointProduct)
            .where(PointProduct.id == order.product_id)
            .with_for_update()
        )
        product = product_result.scalar_one_or_none()
        if product and not product.stock_unlimited:
            product.stock += 1

        order.status = "cancelled"
        order.admin_id = admin_id
        order.processed_at = datetime.utcnow()
        order.notes_admin = notes
    else:
        raise ValidationException("无效的操作", details={"action": action})

    await db.commit()
    await db.refresh(order)
    return order
