"""
Test FirstSalaryUsage model and schemas
"""
import pytest
from datetime import datetime
from app.models.first_salary_usage import FirstSalaryUsage
from app.schemas.first_salary_usage import (
    FirstSalaryUsageCreate,
    FirstSalaryUsageUpdate,
    FirstSalaryUsageResponse,
)


class TestFirstSalaryUsageModel:
    """测试 FirstSalaryUsage 模型"""

    def test_first_salary_usage_record_creation(self):
        """Test creating a FirstSalaryUsage instance"""
        record = FirstSalaryUsage(
            id="test_id",
            user_id="user_123",
            salary_record_id="salary_456",
            usage_category="存起来",
            usage_subcategory="银行存款",
            amount='{"encrypted":"test","salt":"test"}',  # 加密格式
            note="第一笔工资存银行"
        )
        assert record.usage_category == "存起来"
        assert record.usage_subcategory == "银行存款"
        assert record.amount == '{"encrypted":"test","salt":"test"}'
        assert record.note == "第一笔工资存银行"

    def test_first_salary_usage_record_without_subcategory(self):
        """Test FirstSalaryUsage without optional subcategory"""
        record = FirstSalaryUsage(
            id="test_id",
            user_id="user_123",
            salary_record_id="salary_456",
            usage_category="交家里",
            amount='{"encrypted":"test","salt":"test"}'
        )
        assert record.usage_subcategory is None
        assert record.amount == '{"encrypted":"test","salt":"test"}'

    def test_first_salary_usage_record_without_note(self):
        """Test FirstSalaryUsage without optional note"""
        record = FirstSalaryUsage(
            id="test_id",
            user_id="user_123",
            salary_record_id="salary_456",
            usage_category="买东西",
            usage_subcategory="数码产品",
            amount='{"encrypted":"test","salt":"test"}'
        )
        assert record.note is None
        assert record.amount == '{"encrypted":"test","salt":"test"}'

    def test_first_salary_usage_has_timestamps(self):
        """Test that FirstSalaryUsage has created_at and updated_at columns"""
        # SQLAlchemy default values are only applied on persist, not on instantiation
        # We test that the columns exist in the model
        from datetime import datetime
        record = FirstSalaryUsage(
            id="test_id",
            user_id="user_123",
            salary_record_id="salary_456",
            usage_category="存起来",
            amount='{"encrypted":"test","salt":"test"}',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert record.created_at is not None
        assert record.updated_at is not None
        assert isinstance(record.created_at, datetime)
        assert isinstance(record.updated_at, datetime)


class TestFirstSalaryUsageSchemas:
    """测试 FirstSalaryUsage Pydantic Schemas"""

    def test_create_schema_valid_data(self):
        """Test FirstSalaryUsageCreate with valid data"""
        data = {
            "usage_category": "存起来",
            "usage_subcategory": "银行存款",
            "amount": 2000.00,
            "note": "第一笔工资",
            "salary_record_id": "salary_123"
        }
        schema = FirstSalaryUsageCreate(**data)
        assert schema.usage_category == "存起来"
        assert schema.amount == 2000.00
        assert schema.salary_record_id == "salary_123"

    def test_create_schema_validation_negative_amount(self):
        """Test that negative amounts are rejected"""
        data = {
            "usage_category": "存起来",
            "amount": -100.00,
            "salary_record_id": "salary_123"
        }
        with pytest.raises(ValueError):
            FirstSalaryUsageCreate(**data)

    def test_create_schema_validation_zero_amount(self):
        """Test that zero amounts are rejected"""
        data = {
            "usage_category": "存起来",
            "amount": 0.0,
            "salary_record_id": "salary_123"
        }
        with pytest.raises(ValueError):
            FirstSalaryUsageCreate(**data)

    def test_create_schema_missing_required_field(self):
        """Test that missing required fields are rejected"""
        data = {
            "usage_category": "存起来",
            "salary_record_id": "salary_123"
            # missing amount
        }
        with pytest.raises(ValueError):
            FirstSalaryUsageCreate(**data)

    def test_update_schema_partial_data(self):
        """Test FirstSalaryUsageUpdate with partial data"""
        data = {
            "amount": 3000.00
        }
        schema = FirstSalaryUsageUpdate(**data)
        assert schema.amount == 3000.00
        assert schema.usage_category is None
        assert schema.usage_subcategory is None

    def test_update_schema_all_fields(self):
        """Test FirstSalaryUsageUpdate with all fields"""
        data = {
            "usage_category": "买东西",
            "usage_subcategory": "数码产品",
            "amount": 1500.00,
            "note": "买手机"
        }
        schema = FirstSalaryUsageUpdate(**data)
        assert schema.usage_category == "买东西"
        assert schema.amount == 1500.00

    def test_response_schema(self):
        """Test FirstSalaryUsageResponse"""
        data = {
            "id": "test_id",
            "salary_record_id": "salary_123",
            "usage_category": "存起来",
            "usage_subcategory": "银行存款",
            "amount": 2000.00,
            "note": "第一笔工资",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        schema = FirstSalaryUsageResponse(**data)
        assert schema.id == "test_id"
        assert schema.amount == 2000.00
        assert isinstance(schema.created_at, datetime)

    def test_create_schema_note_max_length(self):
        """Test that note respects max length"""
        long_note = "x" * 501  # 超过最大长度
        data = {
            "usage_category": "存起来",
            "amount": 1000.00,
            "note": long_note,
            "salary_record_id": "salary_123"
        }
        with pytest.raises(ValueError):
            FirstSalaryUsageCreate(**data)
