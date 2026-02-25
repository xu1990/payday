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
        **kwargs
    ) -> UserAddress:
        """
        更新地址信息

        Args:
            db: 数据库会话
            address_id: 地址ID
            **kwargs: 要更新的字段（contact_name, contact_phone, detailed_address等）

        Returns:
            更新后的地址对象

        Raises:
            NotFoundException: 地址不存在
        """
        # 先获取地址
        address = await UserAddressService.get_address(db, address_id)

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(address, key) and value is not None:
                setattr(address, key, value)

        # 提交更改
        await db.commit()
        await db.refresh(address)

        return address

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
