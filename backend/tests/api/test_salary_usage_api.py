"""
薪资使用记录 API 集成测试
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestSalaryUsageAPI:
    """测试薪资使用记录API"""

    async def test_create_salary_usage(
        self, async_client, user_headers: dict, test_salary
    ):
        """测试创建薪资使用记录"""
        usage_data = {
            "salary_record_id": test_salary.id,
            "usage_type": "food",
            "amount": 150.50,
            "usage_date": "2026-02-20T12:00:00",
            "description": "午餐和晚餐"
        }
        response = await async_client.post(
            "/api/v1/salary-usage",
            headers=user_headers,
            json=usage_data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert data["amount"] == 150.50
        assert data["usage_type"] == "food"
        assert data["salary_record_id"] == test_salary.id
        assert "id" in data

    async def test_create_salary_usage_without_auth(self, async_client, test_salary):
        """测试未认证时创建薪资使用记录"""
        usage_data = {
            "salary_record_id": test_salary.id,
            "usage_type": "food",
            "amount": 150.50,
            "usage_date": "2026-02-20T12:00:00"
        }
        response = await async_client.post(
            "/api/v1/salary-usage",
            json=usage_data
        )

        assert response.status_code == 401

    async def test_create_salary_usage_invalid_salary(
        self, async_client, user_headers: dict
    ):
        """测试创建薪资使用记录时使用不存在的薪资记录"""
        usage_data = {
            "salary_record_id": "nonexistent_id",
            "usage_type": "food",
            "amount": 150.50,
            "usage_date": "2026-02-20T12:00:00"
        }
        response = await async_client.post(
            "/api/v1/salary-usage",
            headers=user_headers,
            json=usage_data
        )

        assert response.status_code == 404

    async def test_get_salary_usage(
        self,
        async_client,
        user_headers: dict,
        db_session: AsyncSession,
        test_user,
        test_salary
    ):
        """测试获取单条薪资使用记录"""
        # First create a usage record
        from app.models.salary_usage import SalaryUsageRecord
        from app.services.salary_usage_service import _encrypt_with_salt

        usage = SalaryUsageRecord(
            user_id=test_user.id,
            salary_record_id=test_salary.id,
            usage_type="transport",
            amount=_encrypt_with_salt(50.0),
            usage_date=datetime.now(),
            description="地铁充值"
        )
        db_session.add(usage)
        await db_session.commit()
        await db_session.refresh(usage)

        response = await async_client.get(
            f"/api/v1/salary-usage/{usage.id}",
            headers=user_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert data["id"] == usage.id
        assert data["usage_type"] == "transport"
        assert data["amount"] == 50.0

    async def test_get_salary_usage_not_found(self, async_client, user_headers: dict):
        """测试获取不存在的薪资使用记录"""
        response = await async_client.get(
            "/api/v1/salary-usage/nonexistent_id",
            headers=user_headers
        )

        assert response.status_code == 404

    async def test_update_salary_usage(
        self,
        async_client,
        user_headers: dict,
        db_session: AsyncSession,
        test_user,
        test_salary
    ):
        """测试更新薪资使用记录"""
        # First create a usage record
        from app.models.salary_usage import SalaryUsageRecord
        from app.services.salary_usage_service import _encrypt_with_salt

        usage = SalaryUsageRecord(
            user_id=test_user.id,
            salary_record_id=test_salary.id,
            usage_type="food",
            amount=_encrypt_with_salt(100.0),
            usage_date=datetime.now(),
            description="测试记录"
        )
        db_session.add(usage)
        await db_session.commit()
        await db_session.refresh(usage)

        # Update the record
        update_data = {
            "amount": 200.0,
            "description": "更新后的描述"
        }
        response = await async_client.put(
            f"/api/v1/salary-usage/{usage.id}",
            headers=user_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert data["amount"] == 200.0
        assert data["description"] == "更新后的描述"

    async def test_delete_salary_usage(
        self,
        async_client,
        user_headers: dict,
        db_session: AsyncSession,
        test_user,
        test_salary
    ):
        """测试删除薪资使用记录"""
        # First create a usage record
        from app.models.salary_usage import SalaryUsageRecord
        from app.services.salary_usage_service import _encrypt_with_salt

        usage = SalaryUsageRecord(
            user_id=test_user.id,
            salary_record_id=test_salary.id,
            usage_type="shopping",
            amount=_encrypt_with_salt(300.0),
            usage_date=datetime.now(),
            description="购物"
        )
        db_session.add(usage)
        await db_session.commit()
        await db_session.refresh(usage)

        response = await async_client.delete(
            f"/api/v1/salary-usage/{usage.id}",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_list_salary_usages(
        self,
        async_client,
        user_headers: dict,
        db_session: AsyncSession,
        test_user,
        test_salary
    ):
        """测试获取薪资使用记录列表"""
        # Create multiple usage records
        from app.models.salary_usage import SalaryUsageRecord
        from app.services.salary_usage_service import _encrypt_with_salt

        for i in range(3):
            usage = SalaryUsageRecord(
                user_id=test_user.id,
                salary_record_id=test_salary.id,
                usage_type=f"type_{i}",
                amount=_encrypt_with_salt(float(100 * (i + 1))),
                usage_date=datetime.now(),
                description=f"记录 {i}"
            )
            db_session.add(usage)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/salary-usage",
            headers=user_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert "total" in data
        assert "items" in data
        assert data["total"] >= 3

    async def test_list_salary_usages_with_filters(
        self,
        async_client,
        user_headers: dict,
        db_session: AsyncSession,
        test_user,
        test_salary
    ):
        """测试使用筛选条件获取薪资使用记录列表"""
        # Create usage records with different types
        from app.models.salary_usage import SalaryUsageRecord
        from app.services.salary_usage_service import _encrypt_with_salt

        usage1 = SalaryUsageRecord(
            user_id=test_user.id,
            salary_record_id=test_salary.id,
            usage_type="food",
            amount=_encrypt_with_salt(100.0),
            usage_date=datetime.now(),
            description="食物"
        )
        usage2 = SalaryUsageRecord(
            user_id=test_user.id,
            salary_record_id=test_salary.id,
            usage_type="transport",
            amount=_encrypt_with_salt(50.0),
            usage_date=datetime.now(),
            description="交通"
        )
        db_session.add(usage1)
        db_session.add(usage2)
        await db_session.commit()

        # Filter by usage_type
        response = await async_client.get(
            "/api/v1/salary-usage?usage_type=food",
            headers=user_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["usage_type"] == "food"

    async def test_get_usage_statistics(
        self,
        async_client,
        user_headers: dict,
        db_session: AsyncSession,
        test_user,
        test_salary
    ):
        """测试按类型统计使用金额"""
        # Create usage records
        from app.models.salary_usage import SalaryUsageRecord
        from app.services.salary_usage_service import _encrypt_with_salt

        usage1 = SalaryUsageRecord(
            user_id=test_user.id,
            salary_record_id=test_salary.id,
            usage_type="food",
            amount=_encrypt_with_salt(100.0),
            usage_date=datetime.now(),
            description="食物"
        )
        usage2 = SalaryUsageRecord(
            user_id=test_user.id,
            salary_record_id=test_salary.id,
            usage_type="food",
            amount=_encrypt_with_salt(50.0),
            usage_date=datetime.now(),
            description="更多食物"
        )
        usage3 = SalaryUsageRecord(
            user_id=test_user.id,
            salary_record_id=test_salary.id,
            usage_type="transport",
            amount=_encrypt_with_salt(30.0),
            usage_date=datetime.now(),
            description="交通"
        )
        db_session.add(usage1)
        db_session.add(usage2)
        db_session.add(usage3)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/salary-usage/statistics/by-type",
            headers=user_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert "statistics" in data
        # Food should be 150.0, transport should be 30.0
        assert data["statistics"].get("food") == 150.0
        assert data["statistics"].get("transport") == 30.0

    async def test_permission_checks(
        self,
        async_client,
        user_headers: dict,
        db_session: AsyncSession,
        test_user,
        test_salary
    ):
        """测试用户只能访问自己的薪资使用记录"""
        from app.models.salary_usage import SalaryUsageRecord
        from app.services.salary_usage_service import _encrypt_with_salt
        from app.models.payday import PaydayConfig
        from tests.test_utils import TestDataFactory

        # Create another user with their own salary record
        other_user = await TestDataFactory.create_user(db_session)
        other_config = PaydayConfig(
            user_id=other_user.id,
            job_name="other job",
            payday=25
        )
        db_session.add(other_config)
        await db_session.commit()
        await db_session.refresh(other_config)

        other_salary = await TestDataFactory.create_salary(
            db_session, other_user.id, other_config.id
        )

        # Create usage record for other user
        usage = SalaryUsageRecord(
            user_id=other_user.id,
            salary_record_id=other_salary.id,
            usage_type="food",
            amount=_encrypt_with_salt(100.0),
            usage_date=datetime.now(),
            description="其他用户的记录"
        )
        db_session.add(usage)
        await db_session.commit()
        await db_session.refresh(usage)

        # Try to access other user's record
        response = await async_client.get(
            f"/api/v1/salary-usage/{usage.id}",
            headers=user_headers
        )

        # Should be forbidden
        assert response.status_code == 403
