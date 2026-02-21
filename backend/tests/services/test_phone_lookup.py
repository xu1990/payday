"""
测试手机号查找表功能
"""
import pytest
from sqlalchemy import select

from app.models.user import User
from app.models.phone_lookup import PhoneLookup, hash_phone_number
from app.services.auth_service import get_user_by_phone, bind_phone_to_user
from app.core.exceptions import NotFoundException, ValidationException


@pytest.mark.asyncio
async def test_hash_phone_number():
    """测试手机号哈希函数"""
    phone1 = "13800138000"
    phone2 = "13800138000"
    phone3 = "13900139000"

    # 相同手机号应产生相同哈希
    hash1 = hash_phone_number(phone1)
    hash2 = hash_phone_number(phone2)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 输出长度

    # 不同手机号应产生不同哈希
    hash3 = hash_phone_number(phone3)
    assert hash1 != hash3


@pytest.mark.asyncio
async def test_bind_phone_creates_lookup(db_session):
    """测试绑定手机号时创建 lookup 记录"""
    # 创建测试用户
    user = User(
        openid="test_openid_phone_lookup",
        anonymous_name="测试用户",
    )
    db_session.add(user)
    await db_session.commit()

    # 绑定手机号
    phone = "13800138001"
    await bind_phone_to_user(db_session, str(user.id), phone)

    # 验证 phone_lookup 记录已创建
    result = await db_session.execute(
        select(PhoneLookup).where(PhoneLookup.user_id == str(user.id))
    )
    lookup = result.scalar_one()

    # 验证哈希值正确
    expected_hash = hash_phone_number(phone)
    assert lookup.phone_hash == expected_hash


@pytest.mark.asyncio
async def test_get_user_by_phone_using_lookup(db_session):
    """测试使用 phone_lookup 表查找用户"""
    # 创建测试用户
    user = User(
        openid="test_openid_get_by_phone",
        anonymous_name="测试用户",
    )
    db_session.add(user)
    await db_session.commit()

    # 绑定手机号
    phone = "13800138002"
    await bind_phone_to_user(db_session, str(user.id), phone)

    # 使用手机号查找用户
    found_user = await get_user_by_phone(db_session, phone)

    # 验证找到正确的用户
    assert found_user is not None
    assert found_user.id == user.id


@pytest.mark.asyncio
async def test_get_user_by_phone_not_found(db_session):
    """测试查找不存在的手机号"""
    # 查找未绑定的手机号
    phone = "19999999999"
    found_user = await get_user_by_phone(db_session, phone)

    # 应返回 None
    assert found_user is None


@pytest.mark.asyncio
async def test_phone_hash_uniqueness(db_session):
    """测试手机号哈希唯一性约束"""
    # 创建两个用户
    user1 = User(openid="test_openid_1", anonymous_name="用户1")
    user2 = User(openid="test_openid_2", anonymous_name="用户2")
    db_session.add_all([user1, user2])
    await db_session.commit()

    # 用户1绑定手机号
    phone = "13800138003"
    await bind_phone_to_user(db_session, str(user1.id), phone)

    # 用户2尝试绑定相同手机号应该失败（唯一约束）
    # 注意：这会在数据库层面抛出异常
    from sqlalchemy.exc import IntegrityError

    user2_phone_lookup = PhoneLookup(
        phone_hash=hash_phone_number(phone),
        user_id=str(user2.id)
    )
    db_session.add(user2_phone_lookup)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_phone_lookup_cascade_delete(db_session):
    """测试用户删除时 phone_lookup 记录被删除（通过直接删除记录）"""
    # 创建用户并绑定手机号
    user = User(openid="test_openid_cascade", anonymous_name="测试用户")
    db_session.add(user)
    await db_session.commit()

    phone = "13800138004"
    await bind_phone_to_user(db_session, str(user.id), phone)

    # 验证 lookup 记录存在
    result = await db_session.execute(
        select(PhoneLookup).where(PhoneLookup.user_id == str(user.id))
    )
    lookup_record = result.scalar_one()
    assert lookup_record is not None

    # 手动删除 lookup 记录（在实际数据库中会由 CASCADE 处理）
    await db_session.delete(lookup_record)
    await db_session.commit()

    # 验证 lookup 记录已删除
    result = await db_session.execute(
        select(PhoneLookup).where(PhoneLookup.user_id == str(user.id))
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_get_user_by_phone_performance_comparison(db_session):
    """对比新旧实现方式的性能差异（概念性测试）"""
    import time

    # 创建多个用户并绑定手机号
    users = []
    for i in range(10):
        user = User(
            openid=f"test_openid_perf_{i}",
            anonymous_name=f"用户{i}"
        )
        db_session.add(user)
        users.append(user)
    await db_session.commit()

    # 绑定手机号
    for i, user in enumerate(users):
        phone = f"1380013{i:04d}"
        await bind_phone_to_user(db_session, str(user.id), phone)

    await db_session.commit()

    # 测试查找最后一个用户的性能
    target_phone = f"1380013{9:04d}"

    start_time = time.time()
    found_user = await get_user_by_phone(db_session, target_phone)
    elapsed_time = time.time() - start_time

    assert found_user is not None

    # 新实现应该在极短时间内完成（< 0.1 秒）
    # 注意：这在实际环境中可能有差异，这里只是概念性验证
    assert elapsed_time < 0.1, f"查找耗时过长: {elapsed_time:.3f}秒"
