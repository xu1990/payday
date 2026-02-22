"""
Test FirstSalaryUsage model
"""
import pytest
from app.models.first_salary_usage import FirstSalaryUsage


def test_first_salary_usage_record_creation():
    """Test creating a FirstSalaryUsage instance"""
    record = FirstSalaryUsage(
        id="test_id",
        user_id="user_123",
        salary_record_id="salary_456",
        usage_category="存起来",
        usage_subcategory="银行存款",
        amount=2000.00,
        note="第一笔工资存银行",
        is_first_salary=1
    )
    assert record.usage_category == "存起来"
    assert record.usage_subcategory == "银行存款"
    assert record.amount == 2000.00
    assert record.note == "第一笔工资存银行"
    assert record.is_first_salary == 1


def test_first_salary_usage_record_without_subcategory():
    """Test FirstSalaryUsage without optional subcategory"""
    record = FirstSalaryUsage(
        id="test_id",
        user_id="user_123",
        salary_record_id="salary_456",
        usage_category="交家里",
        amount=1000.00
    )
    assert record.usage_subcategory is None
    assert record.amount == 1000.00


def test_first_salary_usage_record_without_note():
    """Test FirstSalaryUsage without optional note"""
    record = FirstSalaryUsage(
        id="test_id",
        user_id="user_123",
        salary_record_id="salary_456",
        usage_category="买东西",
        usage_subcategory="数码产品",
        amount=500.00
    )
    assert record.note is None
    assert record.amount == 500.00
