"""
Test First Salary Usage Schemas
"""
import pytest
from app.schemas.first_salary_usage import FirstSalaryUsageCreate, FirstSalaryUsageResponse, FirstSalaryUsageListCreate


def test_first_salary_usage_create_schema():
    """Test FirstSalaryUsageCreate schema validation"""
    data = {
        "usageCategory": "存起来",
        "usageSubcategory": "银行存款",
        "amount": 2000.00,
        "note": "第一笔工资"
    }
    usage = FirstSalaryUsageCreate(**data)
    assert usage.usageCategory == "存起来"
    assert usage.usageSubcategory == "银行存款"
    assert usage.amount == 2000.00


def test_first_salary_usage_create_minimal():
    """Test FirstSalaryUsageCreate without optional fields"""
    data = {
        "usageCategory": "存起来",
        "amount": 2000.00
    }
    usage = FirstSalaryUsageCreate(**data)
    assert usage.usageSubcategory is None
    assert usage.note is None


def test_first_salary_usage_create_invalid_amount():
    """Test FirstSalaryUsageCreate rejects invalid amount"""
    data = {
        "usageCategory": "存起来",
        "amount": -100  # Invalid: must be > 0
    }
    with pytest.raises(ValueError):
        FirstSalaryUsageCreate(**data)


def test_first_salary_usage_response_schema():
    """Test FirstSalaryUsageResponse schema"""
    data = {
        "id": "test_id",
        "salaryRecordId": "salary_123",
        "usageCategory": "存起来",
        "amount": 2000.00,
        "isFirstSalary": True
    }
    response = FirstSalaryUsageResponse(**data)
    assert response.id == "test_id"
    assert response.isFirstSalary is True


def test_first_salary_usage_list_create():
    """Test FirstSalaryUsageListCreate schema"""
    data = {
        "usages": [
            {"usageCategory": "存起来", "amount": 2000.0},
            {"usageCategory": "交家里", "amount": 1000.0}
        ]
    }
    list_create = FirstSalaryUsageListCreate(**data)
    assert len(list_create.usages) == 2
    assert list_create.usages[0].usageCategory == "存起来"
