"""
薪资使用记录模型测试
"""
import pytest
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salary_usage import SalaryUsageRecord
from app.models.user import User
from app.models.salary import SalaryRecord
from app.models.payday import PaydayConfig
from app.utils.encryption import encrypt_amount
from tests.test_utils import TestDataFactory


@pytest.mark.asyncio
async def test_create_salary_usage_record(db_session: AsyncSession):
    """测试创建薪资使用记录"""
    # 创建测试用户
    user = await TestDataFactory.create_user(db_session)

    # 创建发薪日配置
    config = await TestDataFactory.create_payday_config(db_session, user.id)

    # 创建薪资记录
    salary = await TestDataFactory.create_salary(db_session, user.id, config.id)

    # 创建薪资使用记录
    amount_encrypted, _ = encrypt_amount(5000)  # 50.00元
    usage_date = datetime(2026, 2, 15, 12, 0, 0)

    record = SalaryUsageRecord(
        user_id=user.id,
        salary_record_id=salary.id,
        usage_type="food",
        amount=amount_encrypted,
        usage_date=usage_date,
        description="购买午餐和晚餐",
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.rollback()
    await db_session.refresh(record)

    # 验证记录创建成功
    assert record.id is not None
    assert record.user_id == user.id
    assert record.salary_record_id == salary.id
    assert record.usage_type == "food"
    assert record.amount == amount_encrypted
    assert record.usage_date == usage_date
    assert record.description == "购买午餐和晚餐"
    assert record.created_at is not None
    assert record.updated_at is not None


@pytest.mark.asyncio
async def test_salary_usage_record_relationships(db_session: AsyncSession):
    """测试薪资使用记录的关系关联"""
    # 创建测试用户
    user = await TestDataFactory.create_user(db_session)

    # 创建发薪日配置
    config = await TestDataFactory.create_payday_config(db_session, user.id)

    # 创建薪资记录
    salary = await TestDataFactory.create_salary(db_session, user.id, config.id)

    # 创建薪资使用记录
    amount_encrypted, _ = encrypt_amount(10000)  # 100.00元
    record = SalaryUsageRecord(
        user_id=user.id,
        salary_record_id=salary.id,
        usage_type="housing",
        amount=amount_encrypted,
        usage_date=datetime.utcnow(),
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.rollback()
    await db_session.refresh(record)

    # 测试与用户的关系
    assert record.user is not None
    assert record.user.id == user.id

    # 测试与薪资记录的关系
    assert record.salary_record is not None
    assert record.salary_record.id == salary.id


@pytest.mark.asyncio
async def test_salary_usage_type_enum(db_session: AsyncSession):
    """测试使用类型枚举值"""
    user = await TestDataFactory.create_user(db_session)
    config = await TestDataFactory.create_payday_config(db_session, user.id)
    salary = await TestDataFactory.create_salary(db_session, user.id, config.id)

    # 测试所有有效的使用类型
    usage_types = [
        "housing",      # 住房
        "food",         # 食物
        "transport",    # 交通
        "shopping",     # 购物
        "entertainment", # 娱乐
        "medical",      # 医疗
        "education",    # 教育
        "other",        # 其他
    ]

    for usage_type in usage_types:
        amount_encrypted, _ = encrypt_amount(1000)
        record = SalaryUsageRecord(
            user_id=user.id,
            salary_record_id=salary.id,
            usage_type=usage_type,
            amount=amount_encrypted,
            usage_date=datetime.utcnow(),
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.rollback()
        await db_session.refresh(record)

        assert record.usage_type == usage_type


@pytest.mark.asyncio
async def test_salary_usage_amount_encryption(db_session: AsyncSession):
    """测试金额加密字段"""
    user = await TestDataFactory.create_user(db_session)
    config = await TestDataFactory.create_payday_config(db_session, user.id)
    salary = await TestDataFactory.create_salary(db_session, user.id, config.id)

    # 验证金额字段为加密的字符串类型
    amount_encrypted, _ = encrypt_amount(8888)  # 88.88元
    record = SalaryUsageRecord(
        user_id=user.id,
        salary_record_id=salary.id,
        usage_type="shopping",
        amount=amount_encrypted,
        usage_date=datetime.utcnow(),
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.rollback()
    await db_session.refresh(record)

    # 验证金额字段是字符串类型
    assert isinstance(record.amount, str)
    assert len(record.amount) > 0
    # 验证加密后的金额不等于明文
    assert record.amount != "8888"


@pytest.mark.asyncio
async def test_salary_usage_timestamps(db_session: AsyncSession):
    """测试创建时间和更新时间默认值"""
    user = await TestDataFactory.create_user(db_session)
    config = await TestDataFactory.create_payday_config(db_session, user.id)
    salary = await TestDataFactory.create_salary(db_session, user.id, config.id)

    amount_encrypted, _ = encrypt_amount(3000)
    record = SalaryUsageRecord(
        user_id=user.id,
        salary_record_id=salary.id,
        usage_type="transport",
        amount=amount_encrypted,
        usage_date=datetime.utcnow(),
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.rollback()
    await db_session.refresh(record)

    # 验证创建时间自动设置
    assert record.created_at is not None
    assert isinstance(record.created_at, datetime)

    # 验证更新时间自动设置
    assert record.updated_at is not None
    assert isinstance(record.updated_at, datetime)

    # 验证初始时创建时间和更新时间基本相同（允许1秒误差）
    time_diff = abs((record.updated_at - record.created_at).total_seconds())
    assert time_diff < 1.0


@pytest.mark.asyncio
async def test_salary_usage_multiple_records_same_salary(db_session: AsyncSession):
    """测试同一薪资记录下可以有多条使用记录"""
    user = await TestDataFactory.create_user(db_session)
    config = await TestDataFactory.create_payday_config(db_session, user.id)
    salary = await TestDataFactory.create_salary(db_session, user.id, config.id)

    # 为同一薪资记录创建多条使用记录
    records_data = [
        ("food", 5000, "购买食材"),
        ("transport", 2000, "地铁充值"),
        ("housing", 15000, "房租"),
    ]

    created_records = []
    for usage_type, amount, desc in records_data:
        amount_encrypted, _ = encrypt_amount(amount)
        record = SalaryUsageRecord(
            user_id=user.id,
            salary_record_id=salary.id,
            usage_type=usage_type,
            amount=amount_encrypted,
            usage_date=datetime.utcnow(),
            description=desc,
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.rollback()
        await db_session.refresh(record)
        created_records.append(record)

    # 验证所有记录都创建成功
    assert len(created_records) == 3
    for record in created_records:
        assert record.id is not None
        assert record.salary_record_id == salary.id
        assert record.user_id == user.id


@pytest.mark.asyncio
async def test_salary_usage_description_optional(db_session: AsyncSession):
    """测试备注说明为可选字段"""
    user = await TestDataFactory.create_user(db_session)
    config = await TestDataFactory.create_payday_config(db_session, user.id)
    salary = await TestDataFactory.create_salary(db_session, user.id, config.id)

    # 创建不带备注的使用记录
    amount_encrypted, _ = encrypt_amount(1000)
    record = SalaryUsageRecord(
        user_id=user.id,
        salary_record_id=salary.id,
        usage_type="other",
        amount=amount_encrypted,
        usage_date=datetime.utcnow(),
        # 不设置 description
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.rollback()
    await db_session.refresh(record)

    # 验证记录创建成功且 description 为 None
    assert record.id is not None
    assert record.description is None
