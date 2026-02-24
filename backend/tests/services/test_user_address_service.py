"""
UserAddress Service 测试 - 用户地址服务

测试覆盖：
1. list_addresses - 列出用户地址（成功、过滤inactive、按user_id过滤）
2. get_address - 获取单个地址（成功、地址不存在）
3. update_address - 更新地址（成功、地址不存在）
4. set_default_address - 设置默认地址（成功、地址不存在、取消其他默认）
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_address_service import UserAddressService
from app.models.address import UserAddress
from app.core.exceptions import NotFoundException


def create_mock_db():
    """创建mock数据库session"""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    return mock_db


def create_mock_address(address_id: str, user_id: str, is_default: bool = False, is_active: bool = True):
    """创建mock地址对象"""
    address = MagicMock()
    address.id = address_id
    address.user_id = user_id
    address.province_code = "110000"
    address.province_name = "北京市"
    address.city_code = "110100"
    address.city_name = "北京市"
    address.district_code = "110101"
    address.district_name = "东城区"
    address.detailed_address = "某街道123号"
    address.postal_code = "100000"
    address.contact_name = "张三"
    address.contact_phone = "13800138000"
    address.is_default = is_default
    address.is_active = is_active
    address.created_at = datetime.utcnow()
    address.updated_at = datetime.utcnow()
    return address


class TestUserAddressService:
    """UserAddressService测试类"""

    @pytest.mark.asyncio
    async def test_list_addresses_success(self):
        """测试成功列出用户地址"""
        # Arrange
        mock_db = create_mock_db()
        user_id = "user_123"

        address1 = create_mock_address("addr_1", user_id, is_default=True)
        address2 = create_mock_address("addr_2", user_id, is_default=False)

        # Mock scalar return for list
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[address1, address2])
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db.execute.return_value = mock_result

        # Act
        addresses = await UserAddressService.list_addresses(mock_db, user_id)

        # Assert
        assert len(addresses) == 2
        assert addresses[0].id == "addr_1"
        assert addresses[1].id == "addr_2"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_addresses_active_only(self):
        """测试只列出active地址"""
        # Arrange
        mock_db = create_mock_db()
        user_id = "user_123"

        address1 = create_mock_address("addr_1", user_id, is_active=True)
        address2 = create_mock_address("addr_2", user_id, is_active=False)

        # Mock scalar return
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[address1])
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db.execute.return_value = mock_result

        # Act
        addresses = await UserAddressService.list_addresses(mock_db, user_id, active_only=True)

        # Assert
        assert len(addresses) == 1
        assert addresses[0].id == "addr_1"
        assert addresses[0].is_active is True

    @pytest.mark.asyncio
    async def test_get_address_success(self):
        """测试成功获取单个地址"""
        # Arrange
        mock_db = create_mock_db()
        address_id = "addr_123"
        user_id = "user_123"

        mock_address = create_mock_address(address_id, user_id)

        # Mock scalar return for single result
        mock_scalars = MagicMock()
        mock_scalars.first = MagicMock(return_value=mock_address)
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db.execute.return_value = mock_result

        # Act
        address = await UserAddressService.get_address(mock_db, address_id)

        # Assert
        assert address is not None
        assert address.id == address_id
        assert address.user_id == user_id
        assert address.contact_name == "张三"

    @pytest.mark.asyncio
    async def test_get_address_not_found(self):
        """测试获取不存在的地址"""
        # Arrange
        mock_db = create_mock_db()
        address_id = "nonexistent_addr"

        # Mock scalar return for None
        mock_scalars = MagicMock()
        mock_scalars.first = MagicMock(return_value=None)
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            await UserAddressService.get_address(mock_db, address_id)

        assert "地址不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_address_success(self):
        """测试成功更新地址"""
        # Arrange
        mock_db = create_mock_db()
        address_id = "addr_123"
        user_id = "user_123"

        mock_address = create_mock_address(address_id, user_id)

        # Mock scalar return for getting address
        mock_scalars = MagicMock()
        mock_scalars.first = MagicMock(return_value=mock_address)
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db.execute.return_value = mock_result

        # Act
        updated_address = await UserAddressService.update_address(
            mock_db,
            address_id,
            contact_name="李四",
            contact_phone="13900139000",
            detailed_address="新地址456号"
        )

        # Assert
        assert updated_address is not None
        assert updated_address.contact_name == "李四"
        assert updated_address.contact_phone == "13900139000"
        assert updated_address.detailed_address == "新地址456号"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_address_not_found(self):
        """测试更新不存在的地址"""
        # Arrange
        mock_db = create_mock_db()
        address_id = "nonexistent_addr"

        # Mock scalar return for None
        mock_scalars = MagicMock()
        mock_scalars.first = MagicMock(return_value=None)
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            await UserAddressService.update_address(
                mock_db,
                address_id,
                contact_name="李四"
            )

        assert "地址不存在" in str(exc_info.value)
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_default_address_success(self):
        """测试成功设置默认地址"""
        # Arrange
        mock_db = create_mock_db()
        user_id = "user_123"
        new_default_id = "addr_2"

        old_default = create_mock_address("addr_1", user_id, is_default=True)
        new_default = create_mock_address(new_default_id, user_id, is_default=False)

        # Mock execute to return different results based on call
        mock_scalars1 = MagicMock()
        mock_scalars1.all = MagicMock(return_value=[old_default])
        mock_result1 = MagicMock()
        mock_result1.scalars = MagicMock(return_value=mock_scalars1)

        mock_scalars2 = MagicMock()
        mock_scalars2.first = MagicMock(return_value=new_default)
        mock_result2 = MagicMock()
        mock_result2.scalars = MagicMock(return_value=mock_scalars2)

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        # Act
        result = await UserAddressService.set_default_address(mock_db, user_id, new_default_id)

        # Assert
        assert result is not None
        assert result.id == new_default_id
        assert result.is_default is True
        assert old_default.is_default is False
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_default_address_not_found(self):
        """测试设置不存在的地址为默认"""
        # Arrange
        mock_db = create_mock_db()
        user_id = "user_123"
        address_id = "nonexistent_addr"

        # Mock execute - no existing defaults and address not found
        mock_scalars1 = MagicMock()
        mock_scalars1.all = MagicMock(return_value=[])
        mock_result1 = MagicMock()
        mock_result1.scalars = MagicMock(return_value=mock_scalars1)

        mock_scalars2 = MagicMock()
        mock_scalars2.first = MagicMock(return_value=None)
        mock_result2 = MagicMock()
        mock_result2.scalars = MagicMock(return_value=mock_scalars2)

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            await UserAddressService.set_default_address(mock_db, user_id, address_id)

        assert "地址不存在" in str(exc_info.value)
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_default_address_unsets_other_defaults(self):
        """测试设置默认地址会取消其他地址的默认状态"""
        # Arrange
        mock_db = create_mock_db()
        user_id = "user_123"
        new_default_id = "addr_3"

        old_default1 = create_mock_address("addr_1", user_id, is_default=True)
        old_default2 = create_mock_address("addr_2", user_id, is_default=True)
        new_default = create_mock_address(new_default_id, user_id, is_default=False)

        # Mock execute to return different results
        mock_scalars1 = MagicMock()
        mock_scalars1.all = MagicMock(return_value=[old_default1, old_default2])
        mock_result1 = MagicMock()
        mock_result1.scalars = MagicMock(return_value=mock_scalars1)

        mock_scalars2 = MagicMock()
        mock_scalars2.first = MagicMock(return_value=new_default)
        mock_result2 = MagicMock()
        mock_result2.scalars = MagicMock(return_value=mock_scalars2)

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        # Act
        result = await UserAddressService.set_default_address(mock_db, user_id, new_default_id)

        # Assert
        assert result is not None
        assert result.id == new_default_id
        assert result.is_default is True
        assert old_default1.is_default is False
        assert old_default2.is_default is False
        mock_db.commit.assert_called_once()
