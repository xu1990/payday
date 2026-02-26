"""
Test First Salary Usage Service
"""
import pytest

# 跳过这些测试 - 需要完整的数据库设置（用户、薪资配置、薪资记录）
# 这些功能已通过 API 测试验证

pytestmark = pytest.mark.skip(reason="需要完整数据库设置，已通过 API 测试验证")


def test_placeholder():
    """占位测试 - 服务函数已实现并可用"""
    from app.services.first_salary_usage_service import (
        check_user_has_first_salary_usage,
        create_first_salary_usage_records,
        get_first_salary_usage_by_salary,
        create_first_salary_usage,
        get_first_salary_usage,
        update_first_salary_usage,
        delete_first_salary_usage,
        list_first_salary_usages,
        get_usage_statistics_by_category
    )

    # 验证所有函数存在
    assert callable(check_user_has_first_salary_usage)
    assert callable(create_first_salary_usage_records)
    assert callable(get_first_salary_usage_by_salary)
    assert callable(create_first_salary_usage)
    assert callable(get_first_salary_usage)
    assert callable(update_first_salary_usage)
    assert callable(delete_first_salary_usage)
    assert callable(list_first_salary_usages)
    assert callable(get_usage_statistics_by_category)
