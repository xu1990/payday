"""
Point SKU API 端点测试

测试 /api/v1/point-skus/* 路由的HTTP端点：
- POST /admin/point-products/{id}/specifications - 创建规格
- GET /admin/point-products/{id}/specifications - 获取规格列表
- PUT /admin/specifications/{id} - 更新规格
- DELETE /admin/specifications/{id} - 删除规格
- POST /admin/specifications/{id}/values - 创建规格值
- GET /admin/specifications/{id}/values - 获取规格值列表
- PUT /admin/specification-values/{id} - 更新规格值
- DELETE /admin/specification-values/{id} - 删除规格值
- GET /admin/point-products/{id}/skus - 获取SKU列表
- POST /admin/point-products/{id}/skus - 创建SKU
- PUT /admin/skus/{id} - 更新SKU
- DELETE /admin/skus/{id} - 删除SKU
- POST /admin/skus/batch-update - 批量更新SKU
"""
import pytest

# ==================== 规格管理 ====================

class TestCreateSpecificationEndpoint:
    """测试POST /api/v1/admin/point-products/{id}/specifications端点"""

    def test_create_specification_unauthorized(self, client):
        """测试创建规格失败 - 未认证"""
        response = client.post(
            "/api/v1/admin/point-products/product123/specifications",
            json={"name": "颜色"}
        )

        assert response.status_code == 401

    def test_create_specification_user_token(self, client, user_headers):
        """测试创建规格失败 - 普通用户token"""
        response = client.post(
            "/api/v1/admin/point-products/product123/specifications",
            json={"name": "颜色"},
            headers=user_headers
        )

        assert response.status_code in [401, 403]

    def test_create_specification_missing_name(self, client, admin_headers):
        """测试创建规格失败 - 缺少必填字段name"""
        response = client.post(
            "/api/v1/admin/point-products/product123/specifications",
            json={"sort_order": 1},
            headers=admin_headers
        )

        assert response.status_code == 422


class TestListSpecificationsEndpoint:
    """测试GET /api/v1/admin/point-products/{id}/specifications端点"""

    def test_list_specifications_unauthorized(self, client):
        """测试获取规格列表失败 - 未认证"""
        response = client.get("/api/v1/admin/point-products/product123/specifications")

        assert response.status_code == 401


# ==================== 规格值管理 ====================

class TestCreateSpecificationValueEndpoint:
    """测试POST /api/v1/admin/specifications/{id}/values端点"""

    def test_create_spec_value_unauthorized(self, client):
        """测试创建规格值失败 - 未认证"""
        response = client.post(
            "/api/v1/admin/specifications/spec123/values",
            json={"value": "红色"}
        )

        assert response.status_code == 401

    def test_create_spec_value_missing_value(self, client, admin_headers):
        """测试创建规格值失败 - 缺少必填字段value"""
        response = client.post(
            "/api/v1/admin/specifications/spec123/values",
            json={"sort_order": 1},
            headers=admin_headers
        )

        assert response.status_code == 422


# ==================== SKU管理 ====================

class TestListSKUsEndpoint:
    """测试GET /api/v1/admin/point-products/{id}/skus端点"""

    def test_list_skus_unauthorized(self, client):
        """测试获取SKU列表失败 - 未认证"""
        response = client.get("/api/v1/admin/point-products/product123/skus")

        assert response.status_code == 401


class TestCreateSKUEndpoint:
    """测试POST /api/v1/admin/point-products/{id}/skus端点"""

    def test_create_sku_unauthorized(self, client):
        """测试创建SKU失败 - 未认证"""
        response = client.post(
            "/api/v1/admin/point-products/product123/skus",
            json={
                "sku_code": "RED-L",
                "specs": {"颜色": "红色", "尺寸": "L"},
                "stock": 10,
                "points_cost": 100
            }
        )

        assert response.status_code == 401

    def test_create_sku_missing_required_fields(self, client, admin_headers):
        """测试创建SKU失败 - 缺少必填字段"""
        response = client.post(
            "/api/v1/admin/point-products/product123/skus",
            json={
                "sku_code": "RED-L"
                # 缺少 specs, stock, points_cost
            },
            headers=admin_headers
        )

        assert response.status_code == 422

    def test_create_sku_invalid_specs_format(self, client, admin_headers):
        """测试创建SKU失败 - specs格式错误"""
        response = client.post(
            "/api/v1/admin/point-products/product123/skus",
            json={
                "sku_code": "RED-L",
                "specs": "invalid",  # 应该是dict
                "stock": 10,
                "points_cost": 100
            },
            headers=admin_headers
        )

        assert response.status_code == 422


class TestUpdateSKUEndpoint:
    """测试PUT /api/v1/admin/skus/{id}端点"""

    def test_update_sku_unauthorized(self, client):
        """测试更新SKU失败 - 未认证"""
        response = client.put(
            "/api/v1/admin/skus/sku123",
            json={"stock": 20}
        )

        assert response.status_code == 401


class TestDeleteSKUEndpoint:
    """测试DELETE /api/v1/admin/skus/{id}端点"""

    def test_delete_sku_unauthorized(self, client):
        """测试删除SKU失败 - 未认证"""
        response = client.delete("/api/v1/admin/skus/sku123")

        assert response.status_code == 401


class TestBatchUpdateSKUsEndpoint:
    """测试POST /api/v1/admin/skus/batch-update端点"""

    def test_batch_update_skus_unauthorized(self, client):
        """测试批量更新SKU失败 - 未认证"""
        response = client.post(
            "/api/v1/admin/skus/batch-update",
            json={
                "skus": [
                    {"id": "sku1", "stock": 10},
                    {"id": "sku2", "stock": 20}
                ]
            }
        )

        assert response.status_code == 401

    def test_batch_update_skus_missing_data(self, client, admin_headers):
        """测试批量更新SKU失败 - 缺少skus数组"""
        response = client.post(
            "/api/v1/admin/skus/batch-update",
            json={},
            headers=admin_headers
        )

        assert response.status_code == 422

    def test_batch_update_skus_empty_array(self, client, admin_headers):
        """测试批量更新SKU失败 - skus数组为空"""
        response = client.post(
            "/api/v1/admin/skus/batch-update",
            json={"skus": []},
            headers=admin_headers
        )

        assert response.status_code == 422
