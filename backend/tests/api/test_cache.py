"""缓存管理API测试"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import status


@pytest.mark.asyncio
class TestTriggerCachePreheat:
    """测试缓存预热接口"""

    async def test_trigger_cache_preheat_success(self, client, admin_headers: dict, monkeypatch):
        """测试成功触发缓存预热"""
        # Mock the preheat_all function at the API import location
        mock_preheat = AsyncMock(return_value={"hot_posts": 10, "memberships": 3, "themes": 5})
        monkeypatch.setattr("app.api.v1.cache.preheat_all", mock_preheat)

        response = client.post("/api/v1/cache/preheat", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "预热完成" in data["message"]
        assert data["details"] == {"hot_posts": 10, "memberships": 3, "themes": 5}

    async def test_trigger_cache_preheat_with_empty_results(self, client, admin_headers: dict, monkeypatch):
        """测试预热结果为空"""
        mock_preheat = AsyncMock(return_value={})
        monkeypatch.setattr("app.api.v1.cache.preheat_all", mock_preheat)

        response = client.post("/api/v1/cache/preheat", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "预热完成" in data["message"]
        assert data["details"] == {}

    async def test_trigger_cache_preheat_failure(self, client, admin_headers: dict, monkeypatch):
        """测试预热失败"""
        async def mock_error(db):
            raise Exception("Redis connection failed")

        monkeypatch.setattr("app.api.v1.cache.preheat_all", mock_error)

        response = client.post("/api/v1/cache/preheat", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert "失败" in data["message"]
        assert "Redis connection failed" in data["message"]

    async def test_trigger_cache_preheat_requires_admin(self, client):
        """测试需要管理员权限"""
        response = client.post("/api/v1/cache/preheat")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_trigger_cache_preheat_requires_admin_not_user(self, client, user_headers: dict):
        """测试普通用户无法访问"""
        response = client.post("/api/v1/cache/preheat", headers=user_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestGetCacheStats:
    """测试获取缓存统计接口"""

    async def test_get_cache_stats_success(self, client, admin_headers: dict, monkeypatch):
        """测试成功获取缓存统计"""
        # Mock Redis connection
        mock_client = Mock()
        mock_client.info.return_value = {
            "connected_clients": 5,
            "used_memory_human": "1.5M",
            "keyspace": {"db0": {"keys": 100}},
        }

        def mock_from_url(url):
            return mock_client

        import redis
        monkeypatch.setattr(redis, "from_url", mock_from_url)

        response = client.get("/api/v1/cache/stats", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["connected_clients"] == 5
        assert data["used_memory_human"] == "1.5M"
        assert data["total_keys"] == 100
        assert "keyspace" in data

    async def test_get_cache_stats_with_empty_keyspace(self, client, admin_headers: dict, monkeypatch):
        """测试空keyspace"""
        mock_client = Mock()
        mock_client.info.return_value = {
            "connected_clients": 1,
            "used_memory_human": "1M",
            "keyspace": {},
        }

        def mock_from_url(url):
            return mock_client

        import redis
        monkeypatch.setattr(redis, "from_url", mock_from_url)

        response = client.get("/api/v1/cache/stats", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["connected_clients"] == 1
        assert data["total_keys"] == 0

    async def test_get_cache_stats_with_multiple_databases(self, client, admin_headers: dict, monkeypatch):
        """测试多个数据库"""
        mock_client = Mock()
        mock_client.info.return_value = {
            "connected_clients": 10,
            "used_memory_human": "10M",
            "keyspace": {
                "db0": {"keys": 100},
                "db1": {"keys": 50},
            },
        }

        def mock_from_url(url):
            return mock_client

        import redis
        monkeypatch.setattr(redis, "from_url", mock_from_url)

        response = client.get("/api/v1/cache/stats", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_keys"] == 150
        assert data["keyspace"]["db0"]["keys"] == 100
        assert data["keyspace"]["db1"]["keys"] == 50

    async def test_get_cache_stats_requires_admin(self, client):
        """测试需要管理员权限"""
        response = client.get("/api/v1/cache/stats")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_cache_stats_requires_admin_not_user(self, client, user_headers: dict):
        """测试普通用户无法访问"""
        response = client.get("/api/v1/cache/stats", headers=user_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
