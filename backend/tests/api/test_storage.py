"""存储API测试"""
import pytest
from fastapi import status


@pytest.mark.asyncio
class TestGetStorageStatusEndpoint:
    """测试获取存储状态接口"""

    async def test_get_storage_status(self, client):
        """测试获取存储状态（公开接口）"""
        response = client.get("/api/v1/storage/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "provider" in data
        assert "cos_enabled" in data
        assert "oss_enabled" in data
        assert "healthy" in data

    async def test_storage_status_structure(self, client):
        """测试返回结构"""
        response = client.get("/api/v1/storage/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 验证基本结构
        assert isinstance(data, dict)
        assert isinstance(data.get("cos_enabled"), bool)
        assert isinstance(data.get("oss_enabled"), bool)
        assert isinstance(data.get("healthy"), bool)


@pytest.mark.asyncio
class TestGetStorageConfigEndpoint:
    """测试获取存储配置接口"""

    async def test_get_storage_config_as_admin(self, client, admin_headers: dict):
        """测试管理员获取存储配置"""
        response = client.get("/api/v1/storage/config", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "provider" in data
        assert "cos" in data
        assert "oss" in data

    async def test_storage_config_structure(self, client, admin_headers: dict):
        """测试配置返回结构"""
        response = client.get("/api/v1/storage/config", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 验证COS部分
        assert "cos" in data
        cos_data = data["cos"]
        assert "enabled" in cos_data
        assert isinstance(cos_data["enabled"], bool)

        # 验证OSS部分
        assert "oss" in data
        oss_data = data["oss"]
        assert "enabled" in oss_data
        assert isinstance(oss_data["enabled"], bool)

    async def test_get_storage_config_requires_admin(self, client):
        """测试需要管理员权限"""
        response = client.get("/api/v1/storage/config")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_storage_config_requires_admin_not_user(self, client, user_headers: dict):
        """测试普通用户无法访问"""
        response = client.get("/api/v1/storage/config", headers=user_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
