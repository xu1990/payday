"""
运费模板管理API测试 - 管理后台
Shipping Template Management API Tests - Admin Panel
"""
import pytest
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(scope="module")
def admin_user_fixture():
    """管理员用户fixture"""
    return {
        "id": "test-admin-id",
        "username": "admin",
        "email": "admin@test.com",
        "is_admin": True,
        "is_active": True
    }


@pytest.fixture(scope="module")
def admin_token_fixture(admin_user_fixture):
    """管理员JWT token fixture"""
    return create_access_token(
        data={"sub": admin_user_fixture["id"], "scope": "admin"}
    )


@pytest.fixture
def client(admin_token_fixture):
    """测试客户端fixture"""
    def get_db_override():
        # 这里需要返回一个mock的数据库session
        from unittest.mock import AsyncMock
        mock_db = AsyncMock(spec=AsyncSession)
        return mock_db

    # 临时覆盖数据库依赖
    app.dependency_overrides[get_db] = get_db_override

    with TestClient(app) as c:
        # 添加认证头
        c.headers["Authorization"] = f"Bearer {admin_token_fixture}"
        yield c

    # 清除依赖覆盖
    app.dependency_overrides.clear()


class TestShippingTemplatesAPI:
    """运费模板API测试类"""

    def test_list_shipping_templates_empty(self, client):
        """测试获取空的运费模板列表"""
        response = client.get("/admin/shipping-templates")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "success"
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_create_shipping_template_success(self, client):
        """测试成功创建运费模板"""
        template_data = {
            "name": "标准快递",
            "description": "全国标准快递服务",
            "charge_type": "weight",
            "default_first_unit": 1000,
            "default_first_cost": 1000,
            "default_continue_unit": 500,
            "default_continue_cost": 500,
            "free_threshold": 20000,
            "estimate_days_min": 2,
            "estimate_days_max": 5
        }

        response = client.post("/admin/shipping-templates", json=template_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "success"
        assert data["data"]["name"] == "标准快递"
        assert data["data"]["charge_type"] == "weight"
        assert data["data"]["is_active"] is True

    def test_create_shipping_template_missing_required_fields(self, client):
        """测试创建运费模板时缺少必填字段"""
        template_data = {
            "name": "测试模板"
            # 缺少其他必填字段
        }

        response = client.post("/admin/shipping-templates", json=template_data)

        assert response.status_code == 422  # Pydantic验证错误

    def test_get_shipping_template_not_found(self, client):
        """测试获取不存在的运费模板"""
        fake_template_id = "fake-template-id"
        response = client.get(f"/admin/shipping-templates/{fake_template_id}")

        assert response.status_code == 404

    def test_update_shipping_template_success(self, client):
        """测试成功更新运费模板"""
        # 先创建模板
        create_data = {
            "name": "原始名称",
            "charge_type": "weight",
            "default_first_unit": 1000,
            "default_first_cost": 1000,
            "default_continue_unit": 500,
            "default_continue_cost": 500
        }

        create_response = client.post("/admin/shipping-templates", json=create_data)
        template_id = create_response.json()["data"]["id"]

        # 更新模板
        update_data = {
            "name": "更新名称",
            "description": "更新描述",
            "free_threshold": 30000
        }

        response = client.put(f"/admin/shipping-templates/{template_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "success"
        assert data["data"]["name"] == "更新名称"
        assert data["data"]["description"] == "更新描述"
        assert data["data"]["free_threshold"] == 30000

    def test_delete_shipping_template_success(self, client):
        """测试成功删除运费模板"""
        # 先创建模板
        template_data = {
            "name": "待删除模板",
            "charge_type": "weight",
            "default_first_unit": 1000,
            "default_first_cost": 1000,
            "default_continue_unit": 500,
            "default_continue_cost": 500
        }

        create_response = client.post("/admin/shipping-templates", json=template_data)
        template_id = create_response.json()["data"]["id"]

        # 删除模板
        response = client.delete(f"/admin/shipping-templates/{template_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "success"
        assert data["data"]["deleted"] is True

    def test_delete_shipping_template_not_found(self, client):
        """测试删除不存在的运费模板"""
        fake_template_id = "fake-template-id"
        response = client.delete(f"/admin/shipping-templates/{fake_template_id}")

        assert response.status_code == 404


class TestShippingTemplateRegionsAPI:
    """运费模板区域API测试类"""

    def test_list_template_regions_empty(self, client):
        """测试获取空的模板区域列表"""
        # 先创建模板
        template_data = {
            "name": "测试模板",
            "charge_type": "weight",
            "default_first_unit": 1000,
            "default_first_cost": 1000,
            "default_continue_unit": 500,
            "default_continue_cost": 500
        }

        create_response = client.post("/admin/shipping-templates", json=template_data)
        template_id = create_response.json()["data"]["id"]

        # 获取区域列表（应为空）
        response = client.get(f"/admin/shipping-templates/{template_id}/regions")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "success"
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_create_template_region_success(self, client):
        """测试成功创建模板区域"""
        # 先创建模板
        template_data = {
            "name": "测试模板",
            "charge_type": "weight",
            "default_first_unit": 1000,
            "default_first_cost": 1000,
            "default_continue_unit": 500,
            "default_continue_cost": 500
        }

        create_response = client.post("/admin/shipping-templates", json=template_data)
        template_id = create_response.json()["data"]["id"]

        # 创建区域
        region_data = {
            "region_codes": "110000",
            "region_names": "北京",
            "first_unit": 1000,
            "first_cost": 1200,
            "continue_unit": 500,
            "continue_cost": 600,
            "free_threshold": 15000
        }

        response = client.post(f"/admin/shipping-templates/{template_id}/regions", json=region_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "success"
        assert data["data"]["template_id"] == template_id
        assert data["data"]["region_codes"] == "110000"
        assert data["data"]["region_names"] == "北京"
        assert data["data"]["is_active"] is True

    def test_create_template_region_invalid_template(self, client):
        """测试为不存在的模板创建区域"""
        fake_template_id = "fake-template-id"
        region_data = {
            "region_codes": "110000",
            "region_names": "北京",
            "first_unit": 1000,
            "first_cost": 1000,
            "continue_unit": 500,
            "continue_cost": 500
        }

        response = client.post(f"/admin/shipping-templates/{fake_template_id}/regions", json=region_data)

        assert response.status_code == 404

    def test_update_template_region_success(self, client):
        """测试成功更新模板区域"""
        # 先创建模板和区域
        template_data = {
            "name": "测试模板",
            "charge_type": "weight",
            "default_first_unit": 1000,
            "default_first_cost": 1000,
            "default_continue_unit": 500,
            "default_continue_cost": 500
        }

        create_response = client.post("/admin/shipping-templates", json=template_data)
        template_id = create_response.json()["data"]["id"]

        region_data = {
            "region_codes": "110000",
            "region_names": "北京",
            "first_unit": 1000,
            "first_cost": 1000,
            "continue_unit": 500,
            "continue_cost": 500
        }

        create_region_response = client.post(f"/admin/shipping-templates/{template_id}/regions", json=region_data)
        region_id = create_region_response.json()["data"]["id"]

        # 更新区域
        update_data = {
            "first_cost": 1500,
            "free_threshold": 20000
        }

        response = client.put(f"/admin/shipping-template-regions/{region_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "success"
        assert data["data"]["first_cost"] == 1500
        assert data["data"]["free_threshold"] == 20000

    def test_delete_template_region_success(self, client):
        """测试成功删除模板区域"""
        # 先创建模板和区域
        template_data = {
            "name": "测试模板",
            "charge_type": "weight",
            "default_first_unit": 1000,
            "default_first_cost": 1000,
            "default_continue_unit": 500,
            "default_continue_cost": 500
        }

        create_response = client.post("/admin/shipping-templates", json=template_data)
        template_id = create_response.json()["data"]["id"]

        region_data = {
            "region_codes": "110000",
            "region_names": "北京",
            "first_unit": 1000,
            "first_cost": 1000,
            "continue_unit": 500,
            "continue_cost": 500
        }

        create_region_response = client.post(f"/admin/shipping-templates/{template_id}/regions", json=region_data)
        region_id = create_region_response.json()["data"]["id"]

        # 删除区域
        response = client.delete(f"/admin/shipping-template-regions/{region_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "success"
        assert data["data"]["deleted"] is True