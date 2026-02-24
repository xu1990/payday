"""
测试用户地址管理 API 端点 - Task 11
User Address API Endpoints Tests

测试用户地址管理的所有API端点：
- GET /api/v1/admin/user-addresses - 列出地址（支持user_id, phone过滤）
- GET /api/v1/admin/user-addresses/{address_id} - 获取单个地址
- PUT /api/v1/admin/user-addresses/{address_id} - 更新地址
- POST /api/v1/admin/user-addresses/{address_id}/set-default - 设置默认地址
- GET /api/v1/admin/users/{user_id}/addresses - 获取用户的所有地址

测试覆盖：
- 成功场景
- 权限验证（管理员权限）
- 数据验证
- 业务规则验证
- 错误处理
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.deps import get_current_admin
from app.models.admin import AdminUser
from app.models.address import UserAddress
from app.core.exceptions import NotFoundException


# Mock get_current_admin dependency
async def mock_get_current_admin():
    """Mock current admin for testing"""
    admin = AdminUser(
        id="admin-123",
        username="test_admin",
        role="admin",
        is_active="1"
    )
    return admin


class TestListUserAddressesEndpoint:
    """测试列出地址端点"""

    @pytest.mark.asyncio
    async def test_list_addresses_success(self):
        """测试成功列出所有地址（需要提供user_id）"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        address1 = UserAddress(
            id="addr_1",
            user_id="user_123",
            province_code="110000",
            province_name="北京市",
            city_code="110100",
            city_name="北京市",
            district_code="110101",
            district_name="东城区",
            detailed_address="某街道123号",
            postal_code="100000",
            contact_name="张三",
            contact_phone="13800138000",
            is_default=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        address2 = UserAddress(
            id="addr_2",
            user_id="user_123",
            province_code="310000",
            province_name="上海市",
            city_code="310100",
            city_name="上海市",
            district_code="310101",
            district_name="黄浦区",
            detailed_address="某街道456号",
            postal_code="200000",
            contact_name="李四",
            contact_phone="13900139000",
            is_default=False,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            with patch("app.api.v1.admin_address.UserAddressService.list_addresses", new_callable=AsyncMock, return_value=[address1, address2]):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/admin/user-addresses?user_id=user_123",
                        headers={"Authorization": "Bearer admin_token"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["code"] == "SUCCESS"
                    assert data["message"] == "获取地址列表成功"
                    assert len(data["details"]) == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_addresses_empty_without_user_id(self):
        """测试不提供user_id时返回空列表"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/admin/user-addresses",
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["code"] == "SUCCESS"
                assert data["message"] == "获取地址列表成功"
                assert len(data["details"]) == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_addresses_with_user_filter(self):
        """测试按user_id过滤地址"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        address = UserAddress(
            id="addr_1",
            user_id="user_123",
            province_code="110000",
            province_name="北京市",
            city_code="110100",
            city_name="北京市",
            district_code="110101",
            district_name="东城区",
            detailed_address="某街道123号",
            postal_code="100000",
            contact_name="张三",
            contact_phone="13800138000",
            is_default=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            with patch("app.api.v1.admin_address.UserAddressService.list_addresses", new_callable=AsyncMock, return_value=[address]):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/admin/user-addresses?user_id=user_123",
                        headers={"Authorization": "Bearer admin_token"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["code"] == "SUCCESS"
                    assert len(data["details"]) == 1
        finally:
            app.dependency_overrides.clear()


class TestGetUserAddressEndpoint:
    """测试获取单个地址端点"""

    @pytest.mark.asyncio
    async def test_get_address_success(self):
        """测试成功获取单个地址"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        address = UserAddress(
            id="addr_123",
            user_id="user_123",
            province_code="110000",
            province_name="北京市",
            city_code="110100",
            city_name="北京市",
            district_code="110101",
            district_name="东城区",
            detailed_address="某街道123号",
            postal_code="100000",
            contact_name="张三",
            contact_phone="13800138000",
            is_default=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            with patch("app.api.v1.admin_address.UserAddressService.get_address", new_callable=AsyncMock, return_value=address):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/admin/user-addresses/addr_123",
                        headers={"Authorization": "Bearer admin_token"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["code"] == "SUCCESS"
                    assert data["message"] == "获取地址成功"
                    assert data["details"]["id"] == "addr_123"
                    assert data["details"]["contact_name"] == "张三"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_address_not_found(self):
        """测试获取不存在的地址"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        try:
            with patch("app.api.v1.admin_address.UserAddressService.get_address", new_callable=AsyncMock, side_effect=NotFoundException("地址不存在")):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/admin/user-addresses/nonexistent",
                        headers={"Authorization": "Bearer admin_token"}
                    )

                    assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestUpdateUserAddressEndpoint:
    """测试更新地址端点"""

    @pytest.mark.asyncio
    async def test_update_address_success(self):
        """测试成功更新地址"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        updated_address = UserAddress(
            id="addr_123",
            user_id="user_123",
            province_code="110000",
            province_name="北京市",
            city_code="110100",
            city_name="北京市",
            district_code="110101",
            district_name="东城区",
            detailed_address="新地址456号",
            postal_code="100000",
            contact_name="李四",
            contact_phone="13900139000",
            is_default=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            with patch("app.api.v1.admin_address.UserAddressService.update_address", new_callable=AsyncMock, return_value=updated_address):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    request_data = {
                        "contact_name": "李四",
                        "contact_phone": "13900139000",
                        "detailed_address": "新地址456号"
                    }

                    response = await client.put(
                        "/api/v1/admin/user-addresses/addr_123",
                        json=request_data,
                        headers={"Authorization": "Bearer admin_token"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["code"] == "SUCCESS"
                    assert data["message"] == "更新地址成功"
                    assert data["details"]["contact_name"] == "李四"
                    assert data["details"]["contact_phone"] == "13900139000"
                    assert data["details"]["detailed_address"] == "新地址456号"
        finally:
            app.dependency_overrides.clear()


class TestSetDefaultAddressEndpoint:
    """测试设置默认地址端点"""

    @pytest.mark.asyncio
    async def test_set_default_address_success(self):
        """测试成功设置默认地址"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        default_address = UserAddress(
            id="addr_123",
            user_id="user_123",
            province_code="110000",
            province_name="北京市",
            city_code="110100",
            city_name="北京市",
            district_code="110101",
            district_name="东城区",
            detailed_address="某街道123号",
            postal_code="100000",
            contact_name="张三",
            contact_phone="13800138000",
            is_default=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            # Mock both get_address and set_default_address
            with patch("app.api.v1.admin_address.UserAddressService.get_address", new_callable=AsyncMock, return_value=default_address):
                with patch("app.api.v1.admin_address.UserAddressService.set_default_address", new_callable=AsyncMock, return_value=default_address):
                    transport = ASGITransport(app=app)
                    async with AsyncClient(transport=transport, base_url="http://test") as client:
                        response = await client.post(
                            "/api/v1/admin/user-addresses/addr_123/set-default",
                            headers={"Authorization": "Bearer admin_token"}
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert data["code"] == "SUCCESS"
                        assert data["message"] == "设置默认地址成功"
                        assert data["details"]["is_default"] is True
        finally:
            app.dependency_overrides.clear()


class TestGetUserAddressesEndpoint:
    """测试获取用户的所有地址端点"""

    @pytest.mark.asyncio
    async def test_get_user_addresses_success(self):
        """测试成功获取用户的所有地址"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        address1 = UserAddress(
            id="addr_1",
            user_id="user_123",
            province_code="110000",
            province_name="北京市",
            city_code="110100",
            city_name="北京市",
            district_code="110101",
            district_name="东城区",
            detailed_address="某街道123号",
            postal_code="100000",
            contact_name="张三",
            contact_phone="13800138000",
            is_default=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        address2 = UserAddress(
            id="addr_2",
            user_id="user_123",
            province_code="310000",
            province_name="上海市",
            city_code="310100",
            city_name="上海市",
            district_code="310101",
            district_name="黄浦区",
            detailed_address="某街道456号",
            postal_code="200000",
            contact_name="李四",
            contact_phone="13900139000",
            is_default=False,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            with patch("app.api.v1.admin_address.UserAddressService.list_addresses", new_callable=AsyncMock, return_value=[address1, address2]):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/admin/users/user_123/addresses",
                        headers={"Authorization": "Bearer admin_token"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["code"] == "SUCCESS"
                    assert data["message"] == "获取用户地址列表成功"
                    assert len(data["details"]) == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_user_addresses_empty(self):
        """测试获取用户的地址列表为空"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        try:
            with patch("app.api.v1.admin_address.UserAddressService.list_addresses", new_callable=AsyncMock, return_value=[]):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/admin/users/user_123/addresses",
                        headers={"Authorization": "Bearer admin_token"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["code"] == "SUCCESS"
                    assert len(data["details"]) == 0
        finally:
            app.dependency_overrides.clear()
