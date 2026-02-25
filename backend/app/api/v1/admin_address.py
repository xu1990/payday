"""
用户地址管理接口 - 管理后台
Admin User Address Management Endpoints

提供管理员对用户地址的管理功能：
- 列出地址（支持user_id, phone过滤）
- 获取单个地址
- 更新地址
- 设置默认地址
- 获取用户的所有地址
"""
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import NotFoundException, success_response
from app.models.address import UserAddress
from app.models.user import User
from app.schemas.address import UserAddressResponse, UserAddressUpdate
from app.services.user_address_service import UserAddressService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin/user-addresses", tags=["admin-user-address"])


def _address_to_dict(address: UserAddress) -> dict:
    """将地址对象转换为字典"""
    return {
        "id": address.id,
        "user_id": address.user_id,
        "province_code": address.province_code,
        "province_name": address.province_name,
        "city_code": address.city_code,
        "city_name": address.city_name,
        "district_code": address.district_code,
        "district_name": address.district_name,
        "detailed_address": address.detailed_address,
        "postal_code": address.postal_code,
        "contact_name": address.contact_name,
        "contact_phone": address.contact_phone,
        "is_default": bool(address.is_default),
        "is_active": bool(address.is_active),
        "created_at": address.created_at.isoformat() if address.created_at else None,
        "updated_at": address.updated_at.isoformat() if address.updated_at else None,
    }


@router.get("")
async def list_addresses(
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    phone: Optional[str] = Query(None, description="手机号过滤"),
    active_only: bool = Query(False, description="只返回有效地址"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取地址列表（管理员）

    支持按user_id和phone过滤
    """
    # 如果有user_id，直接使用UserAddressService.list_addresses
    if user_id:
        addresses = await UserAddressService.list_addresses(
            db, user_id, active_only=active_only
        )
        # 如果还有phone过滤，在内存中过滤（因为phone字段在地址表中）
        if phone:
            addresses = [addr for addr in addresses if addr.contact_phone == phone]
    else:
        # 如果没有user_id，需要查询所有地址（暂时只支持user_id过滤）
        # 实际应用中可能需要更复杂的查询逻辑
        if phone:
            # 通过phone查询，需要先通过phone找user，这里简化处理
            from sqlalchemy import select

            query = select(UserAddress).where(
                UserAddress.contact_phone == phone
            )
            if active_only:
                query = query.where(UserAddress.is_active == True)

            query = query.order_by(UserAddress.created_at.desc())
            result = await db.execute(query)
            addresses = list(result.scalars().all())
        else:
            # 不带任何过滤，返回空列表（避免返回所有地址）
            addresses = []

    items = [_address_to_dict(addr) for addr in addresses]

    return success_response(data=items, message="获取地址列表成功")


# IMPORTANT: This route must be defined BEFORE /{address_id} to avoid route conflicts
@router.get("/users/{user_id}/addresses")
async def get_user_addresses(
    user_id: str,
    active_only: bool = Query(False, description="只返回有效地址"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定用户的所有地址（管理员）"""
    addresses = await UserAddressService.list_addresses(
        db, user_id, active_only=active_only
    )

    items = [_address_to_dict(addr) for addr in addresses]

    return success_response(
        data=items,
        message="获取用户地址列表成功"
    )


@router.get("/{address_id}")
async def get_address(
    address_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个地址详情（管理员）"""
    address = await UserAddressService.get_address(db, address_id)
    return success_response(
        data=_address_to_dict(address),
        message="获取地址成功"
    )


@router.put("/{address_id}")
async def update_address(
    address_id: str,
    data: UserAddressUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新地址信息（管理员）"""
    # 只传递非None的字段
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    updated_address = await UserAddressService.update_address(
        db, address_id, **update_data
    )

    return success_response(
        data=_address_to_dict(updated_address),
        message="更新地址成功"
    )


@router.post("/{address_id}/set-default")
async def set_default_address(
    address_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    设置默认地址（管理员）

    需要先获取地址的user_id，然后调用service方法
    """
    # 先获取地址以得到user_id
    address = await UserAddressService.get_address(db, address_id)

    # 设置为默认
    default_address = await UserAddressService.set_default_address(
        db, address.user_id, address_id
    )

    return success_response(
        data=_address_to_dict(default_address),
        message="设置默认地址成功"
    )


# Create a separate router for user-specific addresses
users_router = APIRouter(prefix="/admin/users", tags=["admin-user-address"])


@users_router.get("/{user_id}/addresses")
async def get_user_addresses_v2(
    user_id: str,
    active_only: bool = Query(False, description="只返回有效地址"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定用户的所有地址（管理员）"""
    addresses = await UserAddressService.list_addresses(
        db, user_id, active_only=active_only
    )

    items = [_address_to_dict(addr) for addr in addresses]

    return success_response(
        data=items,
        message="获取用户地址列表成功"
    )

