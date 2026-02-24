"""
Test Point Categories API Endpoints - Sprint 4.7
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category(async_client: AsyncClient, admin_token: str):
    """Test creating a category via API"""
    response = await async_client.post(
        "/api/v1/admin/point-categories",
        json={
            "name": "测试分类",
            "level": 1,
            "description": "测试描述"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert "id" in data["details"]


@pytest.mark.asyncio
async def test_get_category_tree(async_client: AsyncClient, admin_token: str):
    """Test getting category tree via API"""
    # First create a category
    await async_client.post(
        "/api/v1/admin/point-categories",
        json={"name": "根分类", "level": 1},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    response = await async_client.get(
        "/api/v1/admin/point-categories/tree",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert len(data["details"]) > 0


@pytest.mark.asyncio
async def test_get_category(async_client: AsyncClient, admin_token: str):
    """Test getting a single category via API"""
    # First create a category
    create_response = await async_client.post(
        "/api/v1/admin/point-categories",
        json={"name": "测试分类", "level": 1},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    category_id = create_response.json()["details"]["id"]

    response = await async_client.get(
        f"/api/v1/admin/point-categories/{category_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert data["details"]["id"] == category_id
    assert data["details"]["name"] == "测试分类"


@pytest.mark.asyncio
async def test_update_category(async_client: AsyncClient, admin_token: str):
    """Test updating a category via API"""
    # First create a category
    create_response = await async_client.post(
        "/api/v1/admin/point-categories",
        json={"name": "原始名称", "level": 1},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    category_id = create_response.json()["details"]["id"]

    response = await async_client.put(
        f"/api/v1/admin/point-categories/{category_id}",
        json={"name": "更新后的名称", "description": "更新后的描述"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
    assert data["details"]["name"] == "更新后的名称"


@pytest.mark.asyncio
async def test_delete_category(async_client: AsyncClient, admin_token: str):
    """Test deleting a category via API"""
    # First create a category
    create_response = await async_client.post(
        "/api/v1/admin/point-categories",
        json={"name": "待删除分类", "level": 1},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    category_id = create_response.json()["details"]["id"]

    response = await async_client.delete(
        f"/api/v1/admin/point-categories/{category_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SUCCESS"
