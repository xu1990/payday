from datetime import datetime

import pytest
from app.schemas.work_record import WorkRecordCreate, WorkRecordResponse
from pydantic import ValidationError


def test_work_record_create_schema():
    """Test WorkRecordCreate schema validation"""
    data = {
        "clock_in_time": "2025-02-24T09:00:00",
        "work_type": "overtime",
        "content": "加班赶项目",
        "mood": "tired",
        "tags": ["加班", "赶项目"],
        "images": ["https://example.com/image.jpg"]
    }

    schema = WorkRecordCreate(**data)

    assert schema.work_type == "overtime"
    assert schema.mood == "tired"
    assert schema.tags == ["加班", "赶项目"]

def test_work_record_create_invalid_type():
    """Test that invalid work type raises error"""
    data = {
        "clock_in_time": "2025-02-24T09:00:00",
        "work_type": "invalid_type",  # Invalid
        "content": "Test"
    }

    with pytest.raises(ValidationError):
        WorkRecordCreate(**data)

def test_work_record_response_schema():
    """Test WorkRecordResponse schema"""
    data = {
        "id": "work-1",
        "user_id": "user-1",
        "post_id": "post-1",
        "clock_in_time": "2025-02-24T09:00:00",
        "work_type": "overtime",
        "overtime_hours": 2.5,
        "content": "加班",
        "created_at": "2025-02-24T09:00:00",
        "updated_at": "2025-02-24T09:00:00"
    }

    schema = WorkRecordResponse(**data)

    assert schema.id == "work-1"
    assert schema.overtime_hours == 2.5
