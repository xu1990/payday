"""
测试薪资使用记录 Schemas
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.salary_usage import (
    SalaryUsageBase,
    SalaryUsageCreate,
    SalaryUsageUpdate,
    SalaryUsageInDB,
    SalaryUsageResponse,
    SalaryUsageListResponse,
)


class TestSalaryUsageCreate:
    """测试创建薪资使用记录 Schema"""

    def test_valid_create(self):
        """测试有效的创建数据"""
        data = {
            "salary_record_id": "salary_123",
            "usage_type": "food",
            "amount": 50.5,
            "usage_date": datetime.now(),
            "description": "午餐"
        }
        schema = SalaryUsageCreate(**data)
        assert schema.salary_record_id == "salary_123"
        assert schema.usage_type == "food"
        assert schema.amount == 50.5
        assert schema.description == "午餐"

    def test_amount_must_be_positive(self):
        """测试金额必须大于0"""
        with pytest.raises(ValidationError) as exc_info:
            SalaryUsageCreate(
                salary_record_id="salary_123",
                usage_type="food",
                amount=0,
                usage_date=datetime.now()
            )
        assert "greater than 0" in str(exc_info.value).lower()

    def test_amount_cannot_be_negative(self):
        """测试金额不能为负数"""
        with pytest.raises(ValidationError) as exc_info:
            SalaryUsageCreate(
                salary_record_id="salary_123",
                usage_type="food",
                amount=-10,
                usage_date=datetime.now()
            )
        assert "greater than 0" in str(exc_info.value).lower()

    def test_valid_usage_types(self):
        """测试所有有效的使用类型"""
        valid_types = [
            "housing", "food", "transport", "shopping",
            "entertainment", "medical", "education", "other"
        ]
        for usage_type in valid_types:
            data = {
                "salary_record_id": "salary_123",
                "usage_type": usage_type,
                "amount": 100,
                "usage_date": datetime.now()
            }
            schema = SalaryUsageCreate(**data)
            assert schema.usage_type == usage_type

    def test_description_max_length(self):
        """测试描述最大长度"""
        long_description = "a" * 501  # 超过500字符
        with pytest.raises(ValidationError) as exc_info:
            SalaryUsageCreate(
                salary_record_id="salary_123",
                usage_type="food",
                amount=100,
                usage_date=datetime.now(),
                description=long_description
            )
        assert "string too long" in str(exc_info.value).lower() or "at most 500 characters" in str(exc_info.value).lower()

    def test_description_can_be_none(self):
        """测试描述可以为None"""
        schema = SalaryUsageCreate(
            salary_record_id="salary_123",
            usage_type="food",
            amount=100,
            usage_date=datetime.now(),
            description=None
        )
        assert schema.description is None

    def test_required_fields(self):
        """测试必填字段"""
        with pytest.raises(ValidationError):
            SalaryUsageCreate(
                salary_record_id="salary_123"
                # 缺少 usage_type, amount, usage_date
            )


class TestSalaryUsageUpdate:
    """测试更新薪资使用记录 Schema"""

    def test_valid_update_all_fields(self):
        """测试更新所有字段"""
        data = {
            "usage_type": "shopping",
            "amount": 200.0,
            "usage_date": datetime.now(),
            "description": "购物"
        }
        schema = SalaryUsageUpdate(**data)
        assert schema.usage_type == "shopping"
        assert schema.amount == 200.0
        assert schema.description == "购物"

    def test_update_partial_fields(self):
        """测试部分字段更新"""
        schema = SalaryUsageUpdate(usage_type="medical")
        assert schema.usage_type == "medical"
        assert schema.amount is None
        assert schema.usage_date is None

    def test_update_amount_must_be_positive(self):
        """测试更新金额必须大于0"""
        with pytest.raises(ValidationError) as exc_info:
            SalaryUsageUpdate(amount=0)
        assert "greater than 0" in str(exc_info.value).lower()

    def test_update_all_fields_optional(self):
        """测试所有字段都是可选的"""
        schema = SalaryUsageUpdate()
        assert schema.usage_type is None
        assert schema.amount is None
        assert schema.usage_date is None
        assert schema.description is None


class TestSalaryUsageResponse:
    """测试薪资使用记录响应 Schema"""

    def test_response_from_attributes(self):
        """测试从ORM模型转换"""
        # 模拟ORM模型对象
        class MockModel:
            id = "usage_123"
            salary_record_id = "salary_789"
            usage_type = "food"
            amount = 50.5  # 响应中应该是解密后的float
            usage_date = datetime.now()
            description = "午餐"
            created_at = datetime.now()
            updated_at = datetime.now()

        mock = MockModel()
        schema = SalaryUsageResponse.model_validate(mock)
        assert schema.id == "usage_123"
        assert schema.amount == 50.5
        assert isinstance(schema.amount, float)


class TestSalaryUsageInDB:
    """测试数据库中的薪资使用记录 Schema"""

    def test_in_db_from_attributes(self):
        """测试从ORM模型转换（InDB格式）"""
        class MockModel:
            id = "usage_123"
            user_id = "user_456"
            salary_record_id = "salary_789"
            usage_type = "food"
            amount = "encrypted_amount_string"  # InDB中是加密后的字符串
            usage_date = datetime.now()
            description = "午餐"
            created_at = datetime.now()
            updated_at = datetime.now()

        mock = MockModel()
        schema = SalaryUsageInDB.model_validate(mock)
        assert schema.id == "usage_123"
        assert schema.amount == "encrypted_amount_string"
        assert isinstance(schema.amount, str)


class TestSalaryUsageListResponse:
    """测试薪资使用记录列表响应 Schema"""

    def test_list_response(self):
        """测试列表响应"""
        # 创建SalaryUsageResponse实例
        item1 = SalaryUsageResponse(
            id="usage_1",
            salary_record_id="salary_123",
            usage_type="food",
            amount=50.0,
            usage_date=datetime.now(),
            description="午餐",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        item2 = SalaryUsageResponse(
            id="usage_2",
            salary_record_id="salary_123",
            usage_type="transport",
            amount=30.0,
            usage_date=datetime.now(),
            description="地铁",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        response = SalaryUsageListResponse(total=2, items=[item1, item2])
        assert response.total == 2
        assert len(response.items) == 2
        assert response.items[0].usage_type == "food"
        assert response.items[1].usage_type == "transport"
