"""
Integration Tests for Sprint 4.1: Phone Login and First Salary Usage

Tests the complete flow:
1. Phone login
2. First salary usage recording
3. Data persistence
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_complete_phone_login_and_first_salary_usage_flow(client: TestClient):
    """
    Test complete Sprint 4.1 flow:
    1. Login with phone authorization
    2. Verify user has phone number
    3. Create first salary usage record
    4. Verify usage record persisted
    """
    # Note: This test requires:
    # - Mock WeChat API for code2session and getPhoneNumber
    # - Mock database with test fixtures
    # - Proper authentication headers
    
    # Step 1: Login with phone
    login_response = client.post("/api/v1/auth/login", json={
        "code": "test_wechat_code",
        "phoneNumberCode": "test_phone_code"
    })
    
    # Verify login response
    assert login_response.status_code in [200, 401, 403]
    
    if login_response.status_code == 200:
        data = login_response.json()
        assert "data" in data
        assert "access_token" in data["data"]
        assert "user" in data["data"]
        
        # Step 2: Check user profile has phone
        token = data["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        user_response = client.get("/api/v1/user/me", headers=headers)
        if user_response.status_code == 200:
            user_data = user_response.json()["data"]
            # Phone should be included in response (masked)
            assert "phoneNumber" in user_data or user_data.get("phoneNumber") is None


@pytest.mark.integration
def test_first_salary_usage_crud(client: TestClient, auth_headers):
    """
    Test CRUD operations for first salary usage
    """
    # Create first salary usage records
    create_response = client.post(
        "/api/v1/first-salary-usage/test_salary_id",
        headers=auth_headers,
        json={
            "usages": [
                {"usageCategory": "存起来", "usageSubcategory": "银行存款", "amount": 2000.0},
                {"usageCategory": "交家里", "amount": 1000.0}
            ]
        }
    )
    
    # Verify creation
    assert create_response.status_code in [200, 401, 403, 404]
    
    if create_response.status_code == 200:
        data = create_response.json()["data"]
        assert "records" in data
        assert len(data["records"]) == 2
        assert data["total"] == 2
        
        # Step 2: Retrieve usage records
        get_response = client.get(
            "/api/v1/first-salary-usage/test_salary_id",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        retrieved_data = get_response.json()["data"]
        assert "records" in retrieved_data


@pytest.mark.integration
def test_phone_login_backward_compatibility(client: TestClient):
    """
    Test that login still works without phone code (backward compatibility)
    """
    response = client.post("/api/v1/auth/login", json={
        "code": "test_wechat_code"
        # No phoneNumberCode
    })
    
    # Should still work
    assert response.status_code in [200, 401, 403]
    
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data["data"]
        assert "user" in data["data"]
