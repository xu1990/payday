"""
Test Courier API Endpoints - Sprint 4.7
物流公司管理接口测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_courier(async_client: AsyncClient, admin_token: str):
    """Test creating a courier via API"""
    response = await async_client.post(
        "/api/v1/admin/couriers",
        json={
            "name": "顺丰速运",
            "code": "SF",
            "website": "https://www.sf-express.com",
            "tracking_url": "https://www.sf-express.com/trace/{tracking_number}",
            "supports_cod": True,
            "supports_cold_chain": True,
            "sort_order": 1,
            "is_active": True
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert "id" in data["details"]
    assert data["details"]["name"] == "顺丰速运"
    assert data["details"]["code"] == "SF"


@pytest.mark.asyncio
async def test_create_courier_duplicate_code(async_client: AsyncClient, admin_token: str):
    """Test creating a courier with duplicate code fails"""
    # Create first courier
    await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "顺丰速运", "code": "SF"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Try to create duplicate
    response = await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "顺丰速运2", "code": "sf"},  # lowercase should still fail
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 422  # ValidationException returns 422
    data = response.json()
    assert data["code"] == "DUPLICATE_COURIER_CODE"


@pytest.mark.asyncio
async def test_list_couriers(async_client: AsyncClient, admin_token: str):
    """Test listing all couriers via API"""
    # Create multiple couriers
    await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "顺丰速运", "code": "SF", "sort_order": 2},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "中通快递", "code": "ZTO", "sort_order": 1},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "圆通速递", "code": "YTO", "sort_order": 3, "is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Test list all
    response = await async_client.get(
        "/api/v1/admin/couriers",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert len(data["details"]) == 3

    # Test list active only
    response = await async_client.get(
        "/api/v1/admin/couriers?active_only=true",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert len(data["details"]) == 2


@pytest.mark.asyncio
async def test_list_active_couriers(async_client: AsyncClient, admin_token: str):
    """Test getting active couriers list for dropdowns"""
    # Create couriers
    await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "顺丰速运", "code": "SF", "is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "中通快递", "code": "ZTO", "is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "圆通速递", "code": "YTO", "is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    response = await async_client.get(
        "/api/v1/admin/couriers/active",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert len(data["details"]) == 2
    # Should only return active couriers
    assert all(c["is_active"] for c in data["details"])


@pytest.mark.asyncio
async def test_get_courier(async_client: AsyncClient, admin_token: str):
    """Test getting a single courier via API"""
    # Create a courier
    create_response = await async_client.post(
        "/api/v1/admin/couriers",
        json={
            "name": "顺丰速运",
            "code": "SF",
            "website": "https://www.sf-express.com",
            "supports_cod": True
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    courier_id = create_response.json()["details"]["id"]

    response = await async_client.get(
        f"/api/v1/admin/couriers/{courier_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert data["details"]["id"] == courier_id
    assert data["details"]["name"] == "顺丰速运"
    assert data["details"]["code"] == "SF"
    assert data["details"]["supports_cod"] is True


@pytest.mark.asyncio
async def test_get_courier_not_found(async_client: AsyncClient, admin_token: str):
    """Test getting a non-existent courier"""
    response = await async_client.get(
        "/api/v1/admin/couriers/nonexistent-id",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "COURIER_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_courier(async_client: AsyncClient, admin_token: str):
    """Test updating a courier via API"""
    # Create a courier
    create_response = await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "顺丰速运", "code": "SF", "supports_cod": False},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    courier_id = create_response.json()["details"]["id"]

    # Update courier
    response = await async_client.put(
        f"/api/v1/admin/couriers/{courier_id}",
        json={
            "name": "顺丰速运有限公司",
            "supports_cod": True,
            "supports_cold_chain": True
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert data["details"]["name"] == "顺丰速运有限公司"
    assert data["details"]["supports_cod"] is True
    assert data["details"]["supports_cold_chain"] is True
    # Code should not change
    assert data["details"]["code"] == "SF"


@pytest.mark.asyncio
async def test_update_courier_not_found(async_client: AsyncClient, admin_token: str):
    """Test updating a non-existent courier"""
    response = await async_client.put(
        "/api/v1/admin/couriers/nonexistent-id",
        json={"name": "Updated Name"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "COURIER_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_courier(async_client: AsyncClient, admin_token: str):
    """Test deleting a courier via API"""
    # Create a courier
    create_response = await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "待删除物流", "code": "DEL"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    courier_id = create_response.json()["details"]["id"]

    # Delete courier
    response = await async_client.delete(
        f"/api/v1/admin/couriers/{courier_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert data["details"]["deleted"] is True

    # Verify courier is deleted
    get_response = await async_client.get(
        f"/api/v1/admin/couriers/{courier_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_courier_not_found(async_client: AsyncClient, admin_token: str):
    """Test deleting a non-existent courier"""
    response = await async_client.delete(
        "/api/v1/admin/couriers/nonexistent-id",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "COURIER_NOT_FOUND"


@pytest.mark.asyncio
async def test_courier_code_auto_uppercase(async_client: AsyncClient, admin_token: str):
    """Test that courier code is automatically converted to uppercase"""
    response = await async_client.post(
        "/api/v1/admin/couriers",
        json={"name": "顺丰速运", "code": "sf"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert data["details"]["code"] == "SF"  # Should be uppercase
