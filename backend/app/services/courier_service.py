"""
物流公司服务 - Courier Service

提供物流公司(CourierCompany)的CRUD操作
"""
from typing import List, Optional

from app.core.exceptions import NotFoundException, ValidationException
from app.models.shipping import CourierCompany
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_courier(
    db: AsyncSession,
    name: str,
    code: str,
    website: Optional[str] = None,
    tracking_url: Optional[str] = None,
    supports_cod: bool = False,
    supports_cold_chain: bool = False,
    sort_order: int = 0,
    is_active: bool = True,
) -> CourierCompany:
    """
    创建物流公司

    Args:
        db: 数据库会话
        name: 物流公司名称
        code: 物流公司代码（自动转大写）
        website: 官网地址
        tracking_url: 物流查询URL
        supports_cod: 是否支持货到付款
        supports_cold_chain: 是否支持冷链
        sort_order: 排序顺序
        is_active: 是否启用

    Returns:
        创建的物流公司对象

    Raises:
        ValidationException: 代码重复时抛出
    """
    # Convert code to uppercase
    code = code.upper().strip()

    # Check if code already exists
    existing = await get_courier_by_code(db, code)
    if existing:
        raise ValidationException(
            message=f"物流公司代码 '{code}' 已存在",
            code="DUPLICATE_COURIER_CODE",
            details={"code": code}
        )

    courier = CourierCompany(
        name=name,
        code=code,
        website=website,
        tracking_url=tracking_url,
        supports_cod=supports_cod,
        supports_cold_chain=supports_cold_chain,
        sort_order=sort_order,
        is_active=is_active,
    )

    db.add(courier)
    await db.commit()
    await db.refresh(courier)

    return courier


async def get_courier(db: AsyncSession, courier_id: str) -> CourierCompany:
    """
    根据ID获取物流公司

    Args:
        db: 数据库会话
        courier_id: 物流公司ID

    Returns:
        物流公司对象

    Raises:
        NotFoundException: 物流公司不存在时抛出
    """
    result = await db.execute(
        select(CourierCompany).where(CourierCompany.id == courier_id)
    )
    courier = result.scalar_one_or_none()

    if not courier:
        raise NotFoundException(
            message=f"物流公司不存在",
            code="COURIER_NOT_FOUND",
            details={"courier_id": courier_id}
        )

    return courier


async def get_courier_by_code(db: AsyncSession, code: str) -> Optional[CourierCompany]:
    """
    根据代码获取物流公司

    Args:
        db: 数据库会话
        code: 物流公司代码（不区分大小写）

    Returns:
        物流公司对象，不存在时返回None
    """
    code = code.upper().strip()
    result = await db.execute(
        select(CourierCompany).where(CourierCompany.code == code)
    )
    return result.scalar_one_or_none()


async def list_couriers(
    db: AsyncSession,
    active_only: bool = False,
) -> List[CourierCompany]:
    """
    获取物流公司列表

    Args:
        db: 数据库会话
        active_only: 是否只返回启用的物流公司

    Returns:
        物流公司列表（按sort_order升序排列）
    """
    query = select(CourierCompany)

    if active_only:
        query = query.where(CourierCompany.is_active == True)

    query = query.order_by(CourierCompany.sort_order.asc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_courier(
    db: AsyncSession,
    courier_id: str,
    **kwargs
) -> CourierCompany:
    """
    更新物流公司信息

    Args:
        db: 数据库会话
        courier_id: 物流公司ID
        **kwargs: 要更新的字段（不包括code）

    Returns:
        更新后的物流公司对象

    Raises:
        NotFoundException: 物流公司不存在时抛出
    """
    courier = await get_courier(db, courier_id)

    # Update fields
    for key, value in kwargs.items():
        if hasattr(courier, key) and key != "id":
            setattr(courier, key, value)

    await db.commit()
    await db.refresh(courier)

    return courier


async def delete_courier(db: AsyncSession, courier_id: str) -> None:
    """
    删除物流公司

    Args:
        db: 数据库会话
        courier_id: 物流公司ID

    Raises:
        NotFoundException: 物流公司不存在时抛出
    """
    courier = await get_courier(db, courier_id)

    await db.delete(courier)
    await db.commit()
