"""
Test First Salary Usage Service
"""
from unittest.mock import AsyncMock, Mock

import pytest
from app.services.first_salary_usage_service import (check_user_has_first_salary_usage,
                                                     create_first_salary_usage_records,
                                                     get_first_salary_usage_by_salary)
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_usage_records(db_session: AsyncSession):
    """Test creating first salary usage records"""
    from app.models.first_salary_usage import FirstSalaryUsage

    # Create mock user and salary record
    user_id = "test_user_123"
    salary_record_id = "test_salary_456"

    usage_data = [
        {"usageCategory": "存起来", "usageSubcategory": "银行存款", "amount": 2000.0, "note": "第一笔工资"},
        {"usageCategory": "交家里", "amount": 1000.0}
    ]

    records = await create_first_salary_usage_records(
        db_session,
        user_id,
        salary_record_id,
        usage_data
    )

    assert len(records) == 2
    assert records[0].usage_category == "存起来"
    assert float(records[0].amount) == 2000.0
    assert records[1].usage_category == "交家里"
    assert float(records[1].amount) == 1000.0


@pytest.mark.asyncio
async def test_check_user_has_usage(db_session: AsyncSession):
    """Test checking if user has first salary usage"""
    user_id = "test_user_123"

    # Initially should be False
    has_usage = await check_user_has_first_salary_usage(db_session, user_id)
    assert has_usage is False

    # After creating records, should be True
    salary_record_id = "test_salary_456"
    usage_data = [{"usageCategory": "存起来", "amount": 2000.0}]
    await create_first_salary_usage_records(
        db_session,
        user_id,
        salary_record_id,
        usage_data
    )

    has_usage = await check_user_has_first_salary_usage(db_session, user_id)
    assert has_usage is True
