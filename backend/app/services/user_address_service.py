"""
UserAddress Service - 用户地址服务

提供用户地址管理功能：
- 列出用户地址
- 获取单个地址
- 更新地址
- 设置默认地址
"""
from typing import List, Optional

from app.core.exceptions import NotFoundException
from app.models.address import UserAddress
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class UserAddressService:
    """用户地址服务类"""

    @staticmethod
    async def list_addresses(
        db: AsyncSession,
        user_id: str,
        active_only: bool = False
    ) -> List[UserAddress]:
        """
        列出用户的所有地址

        Args:
            db: 数据库会话
            user_id: 用户ID
            active_only: 是否只返回有效地址

        Returns:
            地址列表

        Raises:
            无异常，空列表表示没有地址
        """
        query = select(UserAddress).where(UserAddress.user_id == user_id)

        if active_only:
            query = query.where(UserAddress.is_active == True)

        query = query.order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())

        result = await db.execute(query)
        addresses = result.scalars().all()

        return list(addresses)

    @staticmethod
    async def create_address(
        db: AsyncSession,
        user_id: str,
        data: "UserAddressCreate"
    ) -> UserAddress:
        """
        创建新地址

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 地址创建数据

        Returns:
            新创建的地址对象
        """
        # 如果设置为默认地址，先取消其他默认地址
        if data.is_default:
            await db.execute(
                update(UserAddress)
                .where(UserAddress.user_id == user_id, UserAddress.is_default == True)
                .values(is_default=False)
            )

        # 创建新地址
        address = UserAddress(
            user_id=user_id,
            province_code=data.province_code,
            province_name=data.province_name,
            city_code=data.city_code,
            city_name=data.city_name,
            district_code=data.district_code,
            district_name=data.district_name,
            detailed_address=data.detailed_address,
            postal_code=data.postal_code,
            contact_name=data.contact_name,
            contact_phone=data.contact_phone,
            is_default=data.is_default,
            is_active=True,
        )

        db.add(address)
        await db.commit()
        await db.refresh(address)

        return address

    @staticmethod
    async def get_address(
        db: AsyncSession,
        address_id: str
    ) -> UserAddress:
        """
        获取单个地址

        Args:
            db: 数据库会话
            address_id: 地址ID

        Returns:
            地址对象

        Raises:
            NotFoundException: 地址不存在
        """
        query = select(UserAddress).where(UserAddress.id == address_id)

        result = await db.execute(query)
        address = result.scalars().first()

        if not address:
            raise NotFoundException("地址不存在")

        return address

    @staticmethod
    async def update_address(
        db: AsyncSession,
        address_id: str,
        data: "UserAddressUpdate"
    ) -> UserAddress:
        """
        更新地址信息

        Args:
            db: 数据库会话
            address_id: 地址ID
            data: 地址更新数据

        Returns:
            更新后的地址对象

        Raises:
            NotFoundException: 地址不存在
        """
        # 先获取地址
        address = await UserAddressService.get_address(db, address_id)

        # 更新字段（只更新非None的字段）
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in update_data.items():
            if hasattr(address, key):
                setattr(address, key, value)

        # 提交更改
        await db.commit()
        await db.refresh(address)

        return address

    @staticmethod
    async def delete_address(
        db: AsyncSession,
        address_id: str
    ) -> None:
        """
        删除地址（软删除）

        Args:
            db: 数据库会话
            address_id: 地址ID

        Raises:
            NotFoundException: 地址不存在
        """
        # 先获取地址
        address = await UserAddressService.get_address(db, address_id)

        # 软删除：设置 is_active = False
        address.is_active = False

        # 提交更改
        await db.commit()

    @staticmethod
    async def set_default_address(
        db: AsyncSession,
        user_id: str,
        address_id: str
    ) -> UserAddress:
        """
        设置默认地址

        该方法会：
        1. 取消该用户所有其他地址的默认状态
        2. 将指定地址设置为默认

        Args:
            db: 数据库会话
            user_id: 用户ID
            address_id: 要设置为默认的地址ID

        Returns:
            更新后的地址对象

        Raises:
            NotFoundException: 地址不存在
        """
        # 1. 获取用户当前的所有默认地址
        query = select(UserAddress).where(
            UserAddress.user_id == user_id,
            UserAddress.is_default == True
        )
        result = await db.execute(query)
        old_defaults = result.scalars().all()

        # 2. 取消所有旧默认地址的默认状态
        for old_default in old_defaults:
            old_default.is_default = False

        # 3. 获取要设置为默认的地址
        new_default = await UserAddressService.get_address(db, address_id)

        # 验证地址属于该用户
        if new_default.user_id != user_id:
            raise NotFoundException("地址不存在")

        # 4. 设置新的默认地址
        new_default.is_default = True

        # 5. 提交更改
        await db.commit()
        await db.refresh(new_default)

        return new_default
