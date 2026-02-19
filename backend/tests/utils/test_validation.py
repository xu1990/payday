"""测试验证工具"""
import pytest
from uuid import UUID
from app.utils.validation import (
    validate_uuid,
    is_valid_uuid,
    validate_anonymous_name,
    validate_salary_amount,
)
from app.core.exceptions import ValidationException


class TestValidateUUID:
    """测试UUID验证"""

    def test_valid_uuid(self):
        """测试有效UUID"""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = validate_uuid(valid_uuid)
        assert isinstance(result, UUID)

    def test_invalid_uuid(self):
        """测试无效UUID"""
        invalid_uuid = "not-a-uuid"
        with pytest.raises(ValidationException) as exc_info:
            validate_uuid(invalid_uuid)
        assert "无效的ID格式" in str(exc_info.value.message)

    def test_custom_field_name(self):
        """测试自定义字段名"""
        invalid_uuid = "invalid"
        with pytest.raises(ValidationException) as exc_info:
            validate_uuid(invalid_uuid, field_name="user_id")
        assert "user_id" in str(exc_info.value.details["field"])


class TestIsValidUUID:
    """测试UUID快速检查"""

    def test_valid_uuid_returns_true(self):
        """测试有效UUID返回True"""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert is_valid_uuid(valid_uuid) is True

    def test_invalid_uuid_returns_false(self):
        """测试无效UUID返回False"""
        assert is_valid_uuid("not-a-uuid") is False
        assert is_valid_uuid("") is False
        assert is_valid_uuid("123") is False


class TestValidateAnonymousName:
    """测试匿名昵称验证"""

    def test_valid_chinese_name(self):
        """测试有效中文昵称"""
        valid_names = ["张三", "李四", "测试用户", "用户123"]
        for name in valid_names:
            validate_anonymous_name(name)  # 不应抛出异常

    def test_valid_english_name(self):
        """测试有效英文昵称"""
        valid_names = ["Alice", "Bob Smith", "user-123", "test_user"]
        for name in valid_names:
            validate_anonymous_name(name)  # 不应抛出异常

    def test_empty_name(self):
        """测试空昵称"""
        with pytest.raises(ValidationException) as exc_info:
            validate_anonymous_name("")
        assert "长度必须在1-50字符之间" in str(exc_info.value.message)

    def test_too_long_name(self):
        """测试过长昵称"""
        long_name = "a" * 51
        with pytest.raises(ValidationException) as exc_info:
            validate_anonymous_name(long_name)
        assert "长度必须在1-50字符之间" in str(exc_info.value.message)

    def test_invalid_characters(self):
        """测试无效字符"""
        invalid_names = ["用户@#", "test!", "用户$", "user%test"]
        for name in invalid_names:
            with pytest.raises(ValidationException):
                validate_anonymous_name(name)


class TestValidateSalaryAmount:
    """测试工资金额验证"""

    def test_valid_amounts(self):
        """测试有效金额"""
        valid_amounts = [0.01, 100, 1000.50, 999999.99]
        for amount in valid_amounts:
            validate_salary_amount(amount)  # 不应抛出异常

    def test_negative_amount(self):
        """测试负数金额"""
        with pytest.raises(ValidationException) as exc_info:
            validate_salary_amount(-100)
        assert "不能为负数" in str(exc_info.value.message)

    def test_too_small_amount(self):
        """测试过小金额"""
        with pytest.raises(ValidationException) as exc_info:
            validate_salary_amount(0.001)
        assert "超出允许范围" in str(exc_info.value.message)

    def test_too_large_amount(self):
        """测试过大金额"""
        with pytest.raises(ValidationException) as exc_info:
            validate_salary_amount(1000000)
        assert "超出允许范围" in str(exc_info.value.message)
