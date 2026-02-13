"""
工资记录 API 端点测试

测试 /api/v1/salary/* 路由的HTTP端点：
- POST /api/v1/salary - 创建工资记录
- GET /api/v1/salary - 获取用户工资记录列表（分页、筛选）
- GET /api/v1/salary/{id} - 获取工资记录详情
- PUT /api/v1/salary/{id} - 更新工资记录
- DELETE /api/v1/salary/{id} - 删除工资记录
"""
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
class TestCreateSalaryEndpoint:
    """测试POST /api/v1/salary端点"""

    def test_create_salary_success(
        self,
        client,
        user_headers,
        test_user,
        test_salary,
    ):
        """测试创建工资记录成功 - 使用有效数据"""
        # 直接使用test_salary提供的config_id
        config_id = test_salary.config_id

        # 使用TestClient发送HTTP POST请求
        response = client.post(
            "/api/v1/salary",
            json={
                "config_id": config_id,
                "amount": 15000.00,
                "payday_date": "2024-12-25",
                "salary_type": "normal",
                "mood": "happy",
                "note": "年终奖到手",
            },
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["config_id"] == config_id
        assert data["amount"] == 15000.00
        assert data["payday_date"] == "2024-12-25"
        assert data["salary_type"] == "normal"
        assert data["mood"] == "happy"
        assert data["note"] == "年终奖到手"
        assert "id" in data
        assert data["user_id"] == str(test_user.id)

    def test_create_salary_missing_required_fields(
        self,
        client,
        user_headers,
        test_salary,
    ):
        """测试创建工资记录失败 - 缺少必填字段"""
        # 使用TestClient发送HTTP POST请求（缺少amount）
        response = client.post(
            "/api/v1/salary",
            json={
                "config_id": test_salary.config_id,
                "payday_date": "2024-12-25",
                "salary_type": "normal",
                "mood": "happy",
            },
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_salary_invalid_amount(
        self,
        client,
        user_headers,
        test_salary,
    ):
        """测试创建工资记录失败 - 金额格式无效"""
        # 使用TestClient发送HTTP POST请求（金额超过限制）
        response = client.post(
            "/api/v1/salary",
            json={
                "config_id": test_salary.config_id,
                "amount": 99999999.00,  # 超过1000万限制
                "payday_date": "2024-12-25",
                "salary_type": "normal",
                "mood": "happy",
            },
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422

    def test_create_salary_invalid_mood(
        self,
        client,
        user_headers,
        test_salary,
    ):
        """测试创建工资记录失败 - 无效的心情值"""
        # 使用TestClient发送HTTP POST请求（无效的心情）
        response = client.post(
            "/api/v1/salary",
            json={
                "config_id": test_salary.config_id,
                "amount": 10000.00,
                "payday_date": "2024-12-25",
                "salary_type": "normal",
                "mood": "invalid_mood",  # 不在允许的值中
            },
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422

    def test_create_salary_unauthorized(
        self,
        client,
        test_salary,
    ):
        """测试创建工资记录失败 - 未提供认证token"""
        # 使用TestClient发送HTTP POST请求（无认证）
        response = client.post(
            "/api/v1/salary",
            json={
                "config_id": test_salary.config_id,
                "amount": 10000.00,
                "payday_date": "2024-12-25",
                "salary_type": "normal",
                "mood": "happy",
            },
        )

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401


@pytest.mark.asyncio
class TestListSalaryEndpoint:
    """测试GET /api/v1/salary端点"""

    def test_list_salary_success(
        self,
        client,
        user_headers,
        test_user,
        test_salary,
    ):
        """测试获取工资记录列表成功"""
        # 使用TestClient发送HTTP GET请求
        response = client.get("/api/v1/salary", headers=user_headers)

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # 验证返回的数据结构
        assert "id" in data[0]
        assert "amount" in data[0]
        assert "payday_date" in data[0]
        assert "salary_type" in data[0]

    def test_list_salary_with_filters(
        self,
        client,
        user_headers,
        test_salary,
    ):
        """测试获取工资记录列表 - 使用筛选条件"""
        # 使用TestClient发送HTTP GET请求（带日期筛选）
        response = client.get(
            "/api/v1/salary?from_date=2024-01-01&to_date=2024-12-31&limit=10",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_salary_pagination(
        self,
        client,
        user_headers,
        test_salary,
    ):
        """测试获取工资记录列表 - 分页参数"""
        # 使用TestClient发送HTTP GET请求（分页）
        response = client.get("/api/v1/salary?limit=1&offset=0", headers=user_headers)

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 由于limit=1，应该只返回1条记录
        assert len(data) <= 1

    def test_list_salary_unauthorized(
        self,
        client,
        test_salary,
    ):
        """测试获取工资记录列表失败 - 未提供认证token"""
        # 使用TestClient发送HTTP GET请求（无认证）
        response = client.get("/api/v1/salary")

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetSalaryDetailEndpoint:
    """测试GET /api/v1/salary/{id}端点"""

    def test_get_salary_detail_success(
        self,
        client,
        user_headers,
        test_salary,
    ):
        """测试获取工资记录详情成功"""
        # 使用TestClient发送HTTP GET请求
        response = client.get(
            f"/api/v1/salary/{test_salary.id}",
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_salary.id)
        assert "amount" in data
        assert "payday_date" in data
        assert "salary_type" in data
        assert "mood" in data
        assert "created_at" in data

    def test_get_salary_detail_not_found(
        self,
        client,
        user_headers,
    ):
        """测试获取工资记录详情失败 - 记录不存在"""
        # 使用TestClient发送HTTP GET请求（使用不存在的ID）
        response = client.get(
            "/api/v1/salary/non_existent_salary_id",
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回404
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_get_salary_detail_unauthorized(
        self,
        client,
        test_salary,
    ):
        """测试获取工资记录详情失败 - 未提供认证token"""
        # 使用TestClient发送HTTP GET请求（无认证）
        response = client.get(f"/api/v1/salary/{test_salary.id}")

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUpdateSalaryEndpoint:
    """测试PUT /api/v1/salary/{id}端点"""

    def test_update_salary_success(
        self,
        client,
        user_headers,
        test_salary,
    ):
        """测试更新工资记录成功"""
        # 使用TestClient发送HTTP PUT请求
        response = client.put(
            f"/api/v1/salary/{test_salary.id}",
            json={
                "amount": 20000.00,
                "mood": "relief",
                "note": "已更新备注",
            },
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_salary.id)
        assert data["amount"] == 20000.00
        assert data["mood"] == "relief"
        assert data["note"] == "已更新备注"

    def test_update_salary_partial(
        self,
        client,
        user_headers,
        test_salary,
    ):
        """测试部分更新工资记录"""
        # 使用TestClient发送HTTP PUT请求（只更新mood）
        response = client.put(
            f"/api/v1/salary/{test_salary.id}",
            json={"mood": "sad"},
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_salary.id)
        assert data["mood"] == "sad"

    def test_update_salary_not_found(
        self,
        client,
        user_headers,
    ):
        """测试更新工资记录失败 - 记录不存在"""
        # 使用TestClient发送HTTP PUT请求（使用不存在的ID）
        response = client.put(
            "/api/v1/salary/non_existent_salary_id",
            json={"amount": 15000.00},
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回404
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data.get("message", data.get("detail", ""))

    def test_update_salary_invalid_mood(
        self,
        client,
        user_headers,
        test_salary,
    ):
        """测试更新工资记录失败 - 无效的心情值"""
        # 使用TestClient发送HTTP PUT请求（无效的心情）
        response = client.put(
            f"/api/v1/salary/{test_salary.id}",
            json={"mood": "invalid_mood"},
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422

    def test_update_salary_unauthorized(
        self,
        client,
        test_salary,
    ):
        """测试更新工资记录失败 - 未提供认证token"""
        # 使用TestClient发送HTTP PUT请求（无认证）
        response = client.put(
            f"/api/v1/salary/{test_salary.id}",
            json={"amount": 15000.00},
        )

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401


@pytest.mark.asyncio
class TestDeleteSalaryEndpoint:
    """测试DELETE /api/v1/salary/{id}端点"""

    def test_delete_salary_success(
        self,
        client,
        user_headers,
        test_salary,
    ):
        """测试删除工资记录成功"""
        # 使用TestClient发送HTTP DELETE请求
        response = client.delete(
            f"/api/v1/salary/{test_salary.id}",
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回204
        assert response.status_code == 204

        # 验证记录已被删除（再次获取应该返回404）
        get_response = client.get(
            f"/api/v1/salary/{test_salary.id}",
            headers=user_headers,
        )
        assert get_response.status_code == 404

    def test_delete_salary_not_found(
        self,
        client,
        user_headers,
    ):
        """测试删除工资记录失败 - 记录不存在"""
        # 使用TestClient发送HTTP DELETE请求（使用不存在的ID）
        response = client.delete(
            "/api/v1/salary/non_existent_salary_id",
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回404
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_delete_salary_unauthorized(
        self,
        client,
        test_salary,
    ):
        """测试删除工资记录失败 - 未提供认证token"""
        # 使用TestClient发送HTTP DELETE请求（无认证）
        response = client.delete(f"/api/v1/salary/{test_salary.id}")

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401
