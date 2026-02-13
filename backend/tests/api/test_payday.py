"""发薪日配置API测试"""
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.payday_service import create as create_config


@pytest.mark.asyncio
class TestListPaydayConfigs:
    """测试获取发薪日配置列表接口"""

    async def test_list_empty(self, client, test_user: User, user_headers: dict):
        """测试空列表"""
        response = client.get("/api/v1/payday", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    async def test_list_with_configs(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试有配置的列表"""
        # 创建两个配置
        from app.schemas.payday import PaydayConfigCreate
        await create_config(db_session, test_user.id, PaydayConfigCreate(
            job_name="工作A",
            payday=15,
            calendar_type="solar",
        ))
        await create_config(db_session, test_user.id, PaydayConfigCreate(
            job_name="工作B",
            payday=20,
            calendar_type="lunar",
        ))

        response = client.get("/api/v1/payday", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["job_name"] == "工作A"
        assert data[1]["job_name"] == "工作B"

    async def test_list_requires_auth(self, client):
        """测试需要认证"""
        response = client.get("/api/v1/payday")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestCreatePaydayConfig:
    """测试创建发薪日配置接口"""

    async def test_create_success(self, client, test_user: User, user_headers: dict):
        """测试成功创建配置"""
        response = client.post(
            "/api/v1/payday",
            json={
                "job_name": "我的工作",
                "payday": 15,
                "calendar_type": "solar",
                "estimated_salary": 100000,
                "is_active": 1,
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_name"] == "我的工作"
        assert data["payday"] == 15
        assert data["calendar_type"] == "solar"
        assert data["estimated_salary"] == 100000
        assert data["is_active"] == 1
        assert "id" in data
        assert "created_at" in data

    async def test_create_minimal(self, client, test_user: User, user_headers: dict):
        """测试仅提供必填字段"""
        response = client.post(
            "/api/v1/payday",
            json={
                "job_name": "工作",
                "payday": 10,
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_name"] == "工作"
        assert data["payday"] == 10
        assert data["calendar_type"] == "solar"  # 默认值
        assert data["estimated_salary"] is None
        assert data["is_active"] == 1  # 默认值

    async def test_create_with_lunar(self, client, test_user: User, user_headers: dict):
        """测试创建农历配置"""
        response = client.post(
            "/api/v1/payday",
            json={
                "job_name": "农历工作",
                "payday": 15,
                "calendar_type": "lunar",
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["calendar_type"] == "lunar"

    async def test_create_validation_error_job_name_too_long(self, client, test_user: User, user_headers: dict):
        """测试job_name超长"""
        response = client.post(
            "/api/v1/payday",
            json={
                "job_name": "a" * 51,  # 超过50字符
                "payday": 15,
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_validation_error_payday_out_of_range(self, client, test_user: User, user_headers: dict):
        """测试payday超出范围"""
        response = client.post(
            "/api/v1/payday",
            json={
                "job_name": "工作",
                "payday": 32,  # 超过31
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_validation_error_invalid_calendar_type(self, client, test_user: User, user_headers: dict):
        """测试无效的calendar_type"""
        response = client.post(
            "/api/v1/payday",
            json={
                "job_name": "工作",
                "payday": 15,
                "calendar_type": "invalid",
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_validation_error_negative_salary(self, client, test_user: User, user_headers: dict):
        """测试负数工资"""
        response = client.post(
            "/api/v1/payday",
            json={
                "job_name": "工作",
                "payday": 15,
                "estimated_salary": -100,
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_requires_auth(self, client):
        """测试需要认证"""
        response = client.post("/api/v1/payday", json={"job_name": "工作", "payday": 15})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestGetPaydayConfig:
    """测试获取单个发薪日配置接口"""

    async def test_get_existing_config(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试获取已存在的配置"""
        from app.schemas.payday import PaydayConfigCreate
        config = await create_config(db_session, test_user.id, PaydayConfigCreate(
            job_name="我的工作",
            payday=15,
        ))

        response = client.get(f"/api/v1/payday/{config.id}", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == config.id
        assert data["job_name"] == "我的工作"
        assert data["payday"] == 15

    async def test_get_nonexistent_config(self, client, test_user: User, user_headers: dict):
        """测试获取不存在的配置"""
        response = client.get("/api/v1/payday/nonexistent_id", headers=user_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_requires_auth(self, client, db_session: AsyncSession):
        """测试需要认证"""
        from app.schemas.payday import PaydayConfigCreate
        config = await create_config(db_session, "test_user_id", PaydayConfigCreate(
            job_name="工作",
            payday=15,
        ))

        response = client.get(f"/api/v1/payday/{config.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestUpdatePaydayConfig:
    """测试更新发薪日配置接口"""

    async def test_update_job_name(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试更新工作名称"""
        from app.schemas.payday import PaydayConfigCreate
        config = await create_config(db_session, test_user.id, PaydayConfigCreate(
            job_name="原名称",
            payday=15,
        ))

        response = client.put(
            f"/api/v1/payday/{config.id}",
            json={"job_name": "新名称"},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_name"] == "新名称"
        assert data["payday"] == 15  # 未改变

    async def test_update_multiple_fields(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试更新多个字段"""
        from app.schemas.payday import PaydayConfigCreate
        config = await create_config(db_session, test_user.id, PaydayConfigCreate(
            job_name="工作",
            payday=15,
            calendar_type="solar",
        ))

        response = client.put(
            f"/api/v1/payday/{config.id}",
            json={
                "job_name": "新工作",
                "payday": 20,
                "calendar_type": "lunar",
                "estimated_salary": 200000,
                "is_active": 0,
            },
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_name"] == "新工作"
        assert data["payday"] == 20
        assert data["calendar_type"] == "lunar"
        assert data["estimated_salary"] == 200000
        assert data["is_active"] == 0

    async def test_update_nonexistent_config(self, client, test_user: User, user_headers: dict):
        """测试更新不存在的配置"""
        response = client.put(
            "/api/v1/payday/nonexistent_id",
            json={"job_name": "新名称"},
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_validation_errors(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试更新时的验证错误"""
        from app.schemas.payday import PaydayConfigCreate
        config = await create_config(db_session, test_user.id, PaydayConfigCreate(
            job_name="工作",
            payday=15,
        ))

        # payday超出范围
        response = client.put(
            f"/api/v1/payday/{config.id}",
            json={"payday": 32},
            headers=user_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_update_requires_auth(self, client, test_user: User, db_session: AsyncSession):
        """测试需要认证"""
        from app.schemas.payday import PaydayConfigCreate
        config = await create_config(db_session, test_user.id, PaydayConfigCreate(
            job_name="工作",
            payday=15,
        ))

        response = client.put(
            f"/api/v1/payday/{config.id}",
            json={"job_name": "新名称"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestDeletePaydayConfig:
    """测试删除发薪日配置接口"""

    async def test_delete_success(self, client, test_user: User, user_headers: dict, db_session: AsyncSession):
        """测试成功删除配置"""
        from app.schemas.payday import PaydayConfigCreate
        config = await create_config(db_session, test_user.id, PaydayConfigCreate(
            job_name="工作",
            payday=15,
        ))

        response = client.delete(f"/api/v1/payday/{config.id}", headers=user_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_nonexistent_config(self, client, test_user: User, user_headers: dict):
        """测试删除不存在的配置"""
        response = client.delete("/api/v1/payday/nonexistent_id", headers=user_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_requires_auth(self, client, test_user: User, db_session: AsyncSession):
        """测试需要认证"""
        from app.schemas.payday import PaydayConfigCreate
        config = await create_config(db_session, test_user.id, PaydayConfigCreate(
            job_name="工作",
            payday=15,
        ))

        response = client.delete(f"/api/v1/payday/{config.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
