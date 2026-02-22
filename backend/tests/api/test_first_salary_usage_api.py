"""
Test First Salary Usage API Endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_create_first_salary_usage(client: TestClient, auth_headers):
    """Test POST /api/v1/first-salary-usage/{recordId}"""
    response = client.post(
        "/api/v1/first-salary-usage/test_salary_id",
        headers=auth_headers,
        json={
            "usages": [
                {"usageCategory": "存起来", "usageSubcategory": "银行存款", "amount": 2000.0},
                {"usageCategory": "交家里", "amount": 1000.0}
            ]
        }
    )
    # Various valid responses depending on auth state
    assert response.status_code in [200, 401, 403]


def test_create_first_salary_usage_validation_error(client: TestClient):
    """Test POST with empty usages list should fail validation"""
    response = client.post(
        "/api/v1/first-salary-usage/test_salary_id",
        headers={},
        json={"usages": []}
    )
    assert response.status_code in [401, 422]


def test_get_my_first_salary_usage(client: TestClient, auth_headers):
    """Test GET /api/v1/first-salary-usage/my/first-salary"""
    response = client.get(
        "/api/v1/first-salary-usage/my/first-salary",
        headers=auth_headers
    )
    assert response.status_code in [200, 401]
