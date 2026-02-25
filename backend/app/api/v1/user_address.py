"""
用户地址管理接口 - 用户端
User Address Management Endpoints

提供用户对自己地址的管理功能：
- 列出我的地址
- 创建地址
- 更新地址
- 删除地址
- 设置默认地址
"""
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import NotFoundException, ValidationException, success_response
from app.models.address import UserAddress
from app.models.user import User
from app.schemas.address import UserAddressCreate, UserAddressResponse, UserAddressUpdate
from app.services.user_address_service import UserAddressService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/user-addresses", tags=["user-addresses"])


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


@router.get("", response_model=dict)
async def get_my_addresses(
    active_only: bool = Query(False, description="只返回有效地址"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的地址列表"""
    addresses = await UserAddressService.list_addresses(
        db, current_user.id, active_only=active_only
    )

    items = [_address_to_dict(addr) for addr in addresses]

    return success_response(
        data={"items": items, "total": len(items)},
        message="获取地址列表成功"
    )


@router.get("/{address_id}", response_model=dict)
async def get_address(
    address_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取地址详情"""
    address = await UserAddressService.get_address(db, address_id)

    if not address:
        raise NotFoundException("地址不存在")

    # 验证地址属于当前用户
    if address.user_id != current_user.id:
        raise ValidationException("无权访问此地址")

    return success_response(
        data=_address_to_dict(address),
        message="获取地址成功"
    )


@router.post("", response_model=dict)
async def create_address(
    data: UserAddressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新地址"""
    address = await UserAddressService.create_address(
        db, current_user.id, data
    )

    return success_response(
        data=_address_to_dict(address),
        message="添加地址成功"
    )


@router.put("/{address_id}", response_model=dict)
async def update_address(
    address_id: str,
    data: UserAddressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新地址"""
    # 先验证地址存在且属于当前用户
    existing = await UserAddressService.get_address(db, address_id)
    if not existing:
        raise NotFoundException("地址不存在")
    if existing.user_id != current_user.id:
        raise ValidationException("无权修改此地址")

    address = await UserAddressService.update_address(
        db, address_id, data
    )

    return success_response(
        data=_address_to_dict(address),
        message="更新地址成功"
    )


@router.delete("/{address_id}", response_model=dict)
async def delete_address(
    address_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除地址（软删除）"""
    # 先验证地址存在且属于当前用户
    existing = await UserAddressService.get_address(db, address_id)
    if not existing:
        raise NotFoundException("地址不存在")
    if existing.user_id != current_user.id:
        raise ValidationException("无权删除此地址")

    await UserAddressService.delete_address(db, address_id)

    return success_response(
        data={"deleted": True},
        message="删除地址成功"
    )


@router.post("/{address_id}/set-default", response_model=dict)
async def set_default_address(
    address_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """设置默认地址"""
    # 先验证地址存在且属于当前用户
    existing = await UserAddressService.get_address(db, address_id)
    if not existing:
        raise NotFoundException("地址不存在")
    if existing.user_id != current_user.id:
        raise ValidationException("无权修改此地址")

    await UserAddressService.set_default_address(
        db, current_user.id, address_id
    )

    return success_response(
        data={"is_default": True},
        message="设置默认地址成功"
    )
