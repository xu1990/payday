"""
单元测试 - 通用数据模式 (app.schemas.common)
"""
import pytest
from pydantic import ValidationError

from app.schemas.common import IdSchema


class TestIdSchema:
    """测试ID模式"""

    def test_valid_id(self):
        """测试有效的ID"""
        data = IdSchema(id="test_id_123")
        assert data.id == "test_id_123"

    def test_id_serialization(self):
        """测试ID序列化"""
        data = IdSchema(id="user_456")
        json_data = data.model_dump_json()
        assert "user_456" in json_data

    def test_id_from_dict(self):
        """测试从字典创建"""
        data = IdSchema(**{"id": "post_789"})
        assert data.id == "post_789"
