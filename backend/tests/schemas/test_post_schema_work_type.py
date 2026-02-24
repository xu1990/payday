"""Test PostCreate schema accepts work type"""
import pytest
from app.schemas.post import PostCreate
from pydantic import ValidationError


def test_post_create_accepts_work_type():
    """Test that PostCreate schema accepts type='work'"""
    post_data = {
        "content": "今天加班了",
        "type": "work"
    }
    post = PostCreate(**post_data)
    assert post.type == "work"


def test_post_create_defaults_to_complaint():
    """Test that PostCreate schema defaults to complaint"""
    post_data = {
        "content": "测试内容"
    }
    post = PostCreate(**post_data)
    assert post.type == "complaint"


def test_post_create_accepts_all_types():
    """Test that PostCreate schema accepts all valid types"""
    post_data = {
        "content": "测试内容"
    }

    for post_type in ["complaint", "sharing", "question", "work"]:
        post = PostCreate(**{**post_data, "type": post_type})
        assert post.type == post_type


def test_post_create_rejects_invalid_type():
    """Test that PostCreate schema rejects invalid type"""
    post_data = {
        "content": "测试内容",
        "type": "invalid_type"
    }

    with pytest.raises(ValidationError) as exc_info:
        PostCreate(**post_data)

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("type",) for error in errors)
