"""
Admin Config API 端点测试

测试 /api/v1/admin/config/* 路由的HTTP端点：
- GET /api/v1/admin/config/themes - 获取主题列表
- POST /api/v1/admin/config/themes - 创建主题
- PUT /api/v1/admin/config/themes/{id} - 更新主题
- DELETE /api/v1/admin/config/themes/{id} - 删除主题
- GET /api/v1/admin/config/memberships - 获取会员套餐列表
- POST /api/v1/admin/config/memberships - 创建会员套餐
- PUT /api/v1/admin/config/memberships/{id} - 更新会员套餐
- DELETE /api/v1/admin/config/memberships/{id} - 删除会员套餐
- GET /api/v1/admin/config/orders - 获取订单列表
- PUT /api/v1/admin/config/orders/{id} - 更新订单状态

注意：这些测试专注于验证：
1. 端点存在且路由正确
2. 认证和授权要求
3. 请求体验证
4. 基本响应结构

数据库交互的完整测试需要集成测试环境，
这些端点的业务逻辑应该通过服务层单元测试覆盖。
"""
import pytest


# ==================== 主题管理 ====================

class TestThemeListEndpoint:
    """测试GET /api/v1/admin/config/themes端点"""

    def test_list_themes_unauthorized(self, client):
        """测试获取主题列表失败 - 未认证"""
        response = client.get("/api/v1/admin/config/themes")

        # 验证HTTP响应
        assert response.status_code == 401

    def test_list_themes_wrong_token(self, client):
        """测试获取主题列表失败 - 错误的token"""
        response = client.get(
            "/api/v1/admin/config/themes",
            headers={"Authorization": "Bearer invalid_token"}
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]

    def test_list_themes_user_token(self, client, user_headers):
        """测试获取主题列表失败 - 普通用户token"""
        response = client.get("/api/v1/admin/config/themes", headers=user_headers)

        # 验证HTTP响应 - 应该返回401或403（用户无管理员权限）
        assert response.status_code in [401, 403]


class TestThemeCreateEndpoint:
    """测试POST /api/v1/admin/config/themes端点"""

    def test_create_theme_unauthorized(self, client):
        """测试创建主题失败 - 未认证"""
        response = client.post(
            "/api/v1/admin/config/themes",
            json={
                "name": "测试主题",
                "code": "test_theme"
            }
        )

        # 验证HTTP响应
        assert response.status_code == 401

    def test_create_theme_missing_name(self, client, admin_headers):
        """测试创建主题失败 - 缺少必填字段name"""
        response = client.post(
            "/api/v1/admin/config/themes",
            json={
                "code": "test_theme"
            },
            headers=admin_headers
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_theme_missing_code(self, client, admin_headers):
        """测试创建主题失败 - 缺少必填字段code"""
        response = client.post(
            "/api/v1/admin/config/themes",
            json={
                "name": "测试主题"
            },
            headers=admin_headers
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_theme_invalid_name_empty(self, client, admin_headers):
        """测试创建主题失败 - 名称为空字符串"""
        response = client.post(
            "/api/v1/admin/config/themes",
            json={
                "name": "",
                "code": "test_theme"
            },
            headers=admin_headers
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422

    def test_create_theme_user_token(self, client, user_headers):
        """测试创建主题失败 - 普通用户token"""
        response = client.post(
            "/api/v1/admin/config/themes",
            json={
                "name": "测试主题",
                "code": "test_theme"
            },
            headers=user_headers
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestThemeUpdateEndpoint:
    """测试PUT /api/v1/admin/config/themes/{theme_id}端点"""

    def test_update_theme_unauthorized(self, client):
        """测试更新主题失败 - 未认证"""
        response = client.put(
            "/api/v1/admin/config/themes/some_theme_id",
            json={
                "name": "更新后的主题"
            }
        )

        # 验证HTTP响应
        assert response.status_code == 401

    def test_update_theme_user_token(self, client, user_headers):
        """测试更新主题失败 - 普通用户token"""
        response = client.put(
            "/api/v1/admin/config/themes/some_theme_id",
            json={
                "name": "更新后的主题"
            },
            headers=user_headers
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestThemeDeleteEndpoint:
    """测试DELETE /api/v1/admin/config/themes/{theme_id}端点"""

    def test_delete_theme_unauthorized(self, client):
        """测试删除主题失败 - 未认证"""
        response = client.delete("/api/v1/admin/config/themes/some_theme_id")

        # 验证HTTP响应
        assert response.status_code == 401

    def test_delete_theme_user_token(self, client, user_headers):
        """测试删除主题失败 - 普通用户token"""
        response = client.delete(
            "/api/v1/admin/config/themes/some_theme_id",
            headers=user_headers
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


# ==================== 会员套餐管理 ====================

class TestMembershipListEndpoint:
    """测试GET /api/v1/admin/config/memberships端点"""

    def test_list_memberships_unauthorized(self, client):
        """测试获取会员套餐列表失败 - 未认证"""
        response = client.get("/api/v1/admin/config/memberships")

        # 验证HTTP响应
        assert response.status_code == 401

    def test_list_memberships_user_token(self, client, user_headers):
        """测试获取会员套餐列表失败 - 普通用户token"""
        response = client.get("/api/v1/admin/config/memberships", headers=user_headers)

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestMembershipCreateEndpoint:
    """测试POST /api/v1/admin/config/memberships端点"""

    def test_create_membership_unauthorized(self, client):
        """测试创建会员套餐失败 - 未认证"""
        response = client.post(
            "/api/v1/admin/config/memberships",
            json={
                "name": "测试套餐",
                "price": 9900,
                "duration_days": 30
            }
        )

        # 验证HTTP响应
        assert response.status_code == 401

    def test_create_membership_missing_name(self, client, admin_headers):
        """测试创建会员套餐失败 - 缺少必填字段"""
        response = client.post(
            "/api/v1/admin/config/memberships",
            json={
                "price": 9900,
                "duration_days": 30
            },
            headers=admin_headers
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_membership_user_token(self, client, user_headers):
        """测试创建会员套餐失败 - 普通用户token"""
        response = client.post(
            "/api/v1/admin/config/memberships",
            json={
                "name": "测试套餐",
                "price": 9900,
                "duration_days": 30
            },
            headers=user_headers
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestMembershipUpdateEndpoint:
    """测试PUT /api/v1/admin/config/memberships/{membership_id}端点"""

    def test_update_membership_unauthorized(self, client):
        """测试更新会员套餐失败 - 未认证"""
        response = client.put(
            "/api/v1/admin/config/memberships/some_membership_id",
            json={
                "name": "更新后的套餐"
            }
        )

        # 验证HTTP响应
        assert response.status_code == 401

    def test_update_membership_user_token(self, client, user_headers):
        """测试更新会员套餐失败 - 普通用户token"""
        response = client.put(
            "/api/v1/admin/config/memberships/some_membership_id",
            json={
                "name": "更新后的套餐"
            },
            headers=user_headers
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


class TestMembershipDeleteEndpoint:
    """测试DELETE /api/v1/admin/config/memberships/{membership_id}端点"""

    def test_delete_membership_unauthorized(self, client):
        """测试删除会员套餐失败 - 未认证"""
        response = client.delete("/api/v1/admin/config/memberships/some_membership_id")

        # 验证HTTP响应
        assert response.status_code == 401

    def test_delete_membership_user_token(self, client, user_headers):
        """测试删除会员套餐失败 - 普通用户token"""
        response = client.delete(
            "/api/v1/admin/config/memberships/some_membership_id",
            headers=user_headers
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]


# ==================== 订单管理 ====================

class TestOrderListEndpoint:
    """测试GET /api/v1/admin/config/orders端点"""

    def test_list_orders_unauthorized(self, client):
        """测试获取订单列表失败 - 未认证"""
        response = client.get("/api/v1/admin/config/orders")

        # 验证HTTP响应
        assert response.status_code == 401

    def test_list_orders_user_token(self, client, user_headers):
        """测试获取订单列表失败 - 普通用户token"""
        response = client.get("/api/v1/admin/config/orders", headers=user_headers)

        # 验证HTTP响应
        assert response.status_code in [401, 403]

    def test_list_orders_pagination_params(self, client, admin_headers):
        """测试获取订单列表 - 分页参数验证"""
        # 测试无效的limit参数（超出范围）
        response = client.get(
            "/api/v1/admin/config/orders?limit=999",
            headers=admin_headers
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422


class TestOrderUpdateStatusEndpoint:
    """测试PUT /api/v1/admin/config/orders/{order_id}端点"""

    def test_update_order_status_unauthorized(self, client):
        """测试更新订单状态失败 - 未认证"""
        response = client.put(
            "/api/v1/admin/config/orders/some_order_id",
            json={"status": "paid"}
        )

        # 验证HTTP响应
        assert response.status_code == 401

    def test_update_order_status_user_token(self, client, user_headers):
        """测试更新订单状态失败 - 普通用户token"""
        response = client.put(
            "/api/v1/admin/config/orders/some_order_id",
            json={"status": "paid"},
            headers=user_headers
        )

        # 验证HTTP响应
        assert response.status_code in [401, 403]

    def test_update_order_status_missing_status(self, client, admin_headers):
        """测试更新订单状态失败 - 缺少status字段"""
        response = client.put(
            "/api/v1/admin/config/orders/some_order_id",
            json={},
            headers=admin_headers
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422
