"""积分商品SKU服务 - Sprint 4.7 多规格系统"""
from typing import List, Dict, Optional
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.models.point_product import PointProduct
from app.models.point_sku import (
    PointSpecification,
    PointSpecificationValue,
    PointProductSKU,
)
from app.core.exceptions import (
    NotFoundException,
    BusinessException,
    ValidationException,
)


# ============== 规格管理 ==============

async def create_specification(
    db: AsyncSession,
    product_id: str,
    name: str,
    sort_order: int = 0,
) -> PointSpecification:
    """
    创建商品规格

    Args:
        db: 数据库会话
        product_id: 商品ID
        name: 规格名称（如：颜色、尺寸）
        sort_order: 排序权重

    Returns:
        创建的规格对象
    """
    # 验证商品存在
    product_result = await db.execute(
        select(PointProduct).where(PointProduct.id == product_id)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise NotFoundException("商品不存在")

    # 创建规格
    spec = PointSpecification(
        product_id=product_id,
        name=name,
        sort_order=sort_order,
    )
    db.add(spec)
    await db.commit()
    await db.refresh(spec)
    return spec


async def list_specifications(
    db: AsyncSession,
    product_id: str,
) -> List[PointSpecification]:
    """
    获取商品的规格列表

    Args:
        db: 数据库会话
        product_id: 商品ID

    Returns:
        规格列表（按sort_order排序）
    """
    result = await db.execute(
        select(PointSpecification)
        .where(PointSpecification.product_id == product_id)
        .order_by(PointSpecification.sort_order.asc())
    )
    return list(result.scalars().all())


async def delete_specification(
    db: AsyncSession,
    spec_id: str,
) -> bool:
    """
    删除规格

    Args:
        db: 数据库会话
        spec_id: 规格ID

    Returns:
        是否删除成功

    Raises:
        BusinessException: 如果规格下有值
    """
    # 检查规格是否有值
    values_result = await db.execute(
        select(PointSpecificationValue).where(
            PointSpecificationValue.specification_id == spec_id
        )
    )
    values_count = len(values_result.scalars().all())
    if values_count > 0:
        raise BusinessException("规格下有值，无法删除", code="SPEC_HAS_VALUES")

    # 删除规格
    await db.execute(
        delete(PointSpecification).where(PointSpecification.id == spec_id)
    )
    await db.commit()
    return True


# ============== 规格值管理 ==============

async def create_spec_value(
    db: AsyncSession,
    specification_id: str,
    value: str,
    sort_order: int = 0,
) -> PointSpecificationValue:
    """
    创建规格值

    Args:
        db: 数据库会话
        specification_id: 规格ID
        value: 规格值（如：红色、蓝色、L、XL）
        sort_order: 排序权重

    Returns:
        创建的规格值对象
    """
    # 验证规格存在
    spec_result = await db.execute(
        select(PointSpecification).where(
            PointSpecification.id == specification_id
        )
    )
    spec = spec_result.scalar_one_or_none()
    if not spec:
        raise NotFoundException("规格不存在")

    # 创建规格值
    spec_value = PointSpecificationValue(
        specification_id=specification_id,
        value=value,
        sort_order=sort_order,
    )
    db.add(spec_value)
    await db.commit()
    await db.refresh(spec_value)
    return spec_value


async def list_specification_values(
    db: AsyncSession,
    specification_id: str,
) -> List[PointSpecificationValue]:
    """
    获取规格的值列表

    Args:
        db: 数据库会话
        specification_id: 规格ID

    Returns:
        规格值列表（按sort_order排序）
    """
    result = await db.execute(
        select(PointSpecificationValue)
        .where(PointSpecificationValue.specification_id == specification_id)
        .order_by(PointSpecificationValue.sort_order.asc())
    )
    return list(result.scalars().all())


async def delete_spec_value(
    db: AsyncSession,
    value_id: str,
) -> bool:
    """
    删除规格值

    Args:
        db: 数据库会话
        value_id: 规格值ID

    Returns:
        是否删除成功
    """
    await db.execute(
        delete(PointSpecificationValue).where(
            PointSpecificationValue.id == value_id
        )
    )
    await db.commit()
    return True


async def update_specification(
    db: AsyncSession,
    spec_id: str,
    **kwargs
) -> PointSpecification:
    """
    更新规格

    Args:
        db: 数据库会话
        spec_id: 规格ID
        **kwargs: 要更新的字段

    Returns:
        更新后的规格对象
    """
    result = await db.execute(
        select(PointSpecification).where(PointSpecification.id == spec_id)
    )
    spec = result.scalar_one_or_none()

    if not spec:
        raise NotFoundException("规格不存在")

    for key, value in kwargs.items():
        if hasattr(spec, key) and value is not None:
            setattr(spec, key, value)

    await db.commit()
    await db.refresh(spec)
    return spec


async def update_specification_value(
    db: AsyncSession,
    value_id: str,
    **kwargs
) -> PointSpecificationValue:
    """
    更新规格值

    Args:
        db: 数据库会话
        value_id: 规格值ID
        **kwargs: 要更新的字段

    Returns:
        更新后的规格值对象
    """
    result = await db.execute(
        select(PointSpecificationValue).where(PointSpecificationValue.id == value_id)
    )
    spec_value = result.scalar_one_or_none()

    if not spec_value:
        raise NotFoundException("规格值不存在")

    for key, value in kwargs.items():
        if hasattr(spec_value, key) and value is not None:
            setattr(spec_value, key, value)

    await db.commit()
    await db.refresh(spec_value)
    return spec_value


# ============== SKU管理 ==============

async def create_sku(
    db: AsyncSession,
    product_id: str,
    sku_code: str,
    specs: Dict[str, str],
    points_cost: int,
    stock: int = 0,
    stock_unlimited: bool = False,
    image_url: Optional[str] = None,
    sort_order: int = 0,
) -> PointProductSKU:
    """
    创建SKU

    Args:
        db: 数据库会话
        product_id: 商品ID
        sku_code: SKU编码（唯一）
        specs: 规格组合字典（如：{"颜色": "红色", "尺寸": "L"}）
        points_cost: 积分价格
        stock: 库存数量
        stock_unlimited: 是否库存无限
        image_url: SKU专属图片
        sort_order: 排序权重

    Returns:
        创建的SKU对象

    Raises:
        ValidationException: 如果积分价格无效
        BusinessException: 如果SKU编码已存在
    """
    # 验证积分价格
    if points_cost <= 0:
        raise ValidationException("积分价格必须大于0")

    if not stock_unlimited and stock < 0:
        raise ValidationException("库存不能为负数")

    # 验证商品存在
    product_result = await db.execute(
        select(PointProduct).where(PointProduct.id == product_id)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise NotFoundException("商品不存在")

    # 检查SKU编码是否已存在
    existing_result = await db.execute(
        select(PointProductSKU).where(PointProductSKU.sku_code == sku_code)
    )
    if existing_result.scalar_one_or_none():
        raise BusinessException("SKU编码已存在", code="SKU_CODE_EXISTS")

    # 创建SKU
    sku = PointProductSKU(
        product_id=product_id,
        sku_code=sku_code,
        specs=json.dumps(specs, ensure_ascii=False),
        points_cost=points_cost,
        stock=stock,
        stock_unlimited=stock_unlimited,
        image_url=image_url,
        sort_order=sort_order,
        is_active=True,
    )
    db.add(sku)
    await db.commit()
    await db.refresh(sku)
    return sku


async def list_skus(
    db: AsyncSession,
    product_id: str,
    active_only: bool = True,
) -> List[PointProductSKU]:
    """
    获取商品的SKU列表

    Args:
        db: 数据库会话
        product_id: 商品ID
        active_only: 是否只返回启用的SKU

    Returns:
        SKU列表（按sort_order排序）
    """
    query = select(PointProductSKU).where(
        PointProductSKU.product_id == product_id
    )

    if active_only:
        query = query.where(PointProductSKU.is_active == True)

    query = query.order_by(PointProductSKU.sort_order.asc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_sku(
    db: AsyncSession,
    sku_id: str,
    **kwargs
) -> PointProductSKU:
    """
    更新SKU

    Args:
        db: 数据库会话
        sku_id: SKU ID
        **kwargs: 要更新的字段

    Returns:
        更新后的SKU对象
    """
    result = await db.execute(
        select(PointProductSKU).where(PointProductSKU.id == sku_id)
    )
    sku = result.scalar_one_or_none()

    if not sku:
        raise NotFoundException("SKU不存在")

    # 更新字段
    for key, value in kwargs.items():
        if hasattr(sku, key) and value is not None:
            setattr(sku, key, value)

    await db.commit()
    await db.refresh(sku)
    return sku


async def delete_sku(
    db: AsyncSession,
    sku_id: str,
) -> bool:
    """
    删除SKU（软删除，设置is_active=False）

    Args:
        db: 数据库会话
        sku_id: SKU ID

    Returns:
        是否删除成功
    """
    result = await db.execute(
        select(PointProductSKU).where(PointProductSKU.id == sku_id)
    )
    sku = result.scalar_one_or_none()

    if not sku:
        raise NotFoundException("SKU不存在")

    sku.is_active = False
    await db.commit()
    return True


async def batch_update_skus(
    db: AsyncSession,
    updates: List[Dict[str, any]],
) -> bool:
    """
    批量更新SKU

    Args:
        db: 数据库会话
        updates: 更新列表，每项包含id和要更新的字段
                例如：[{"id": "sku1", "stock": 10, "points_cost": 100}]

    Returns:
        是否更新成功

    Raises:
        NotFoundException: 如果任何SKU不存在
    """
    # 验证所有SKU存在
    sku_ids = [item["id"] for item in updates]
    result = await db.execute(
        select(PointProductSKU).where(PointProductSKU.id.in_(sku_ids))
    )
    found_skus = {sku.id: sku for sku in result.scalars().all()}

    # 检查是否有不存在的SKU
    for sku_id in sku_ids:
        if sku_id not in found_skus:
            raise NotFoundException(f"SKU不存在: {sku_id}")

    # 批量更新
    for update_item in updates:
        sku_id = update_item["id"]
        sku = found_skus[sku_id]

        for key, value in update_item.items():
            if key != "id" and hasattr(sku, key):
                setattr(sku, key, value)

    await db.commit()
    return True
