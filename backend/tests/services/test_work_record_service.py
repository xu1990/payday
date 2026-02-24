import pytest
from datetime import datetime
from app.services.work_record_service import WorkRecordService
from app.models.work_record import WorkRecord
from app.models.post import Post
from app.models.user import User
from app.schemas.work_record import WorkRecordCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import random

async def create_test_user(db: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        openid=f"test_openid_{random.randint(1000, 9999)}",
        anonymous_name=f"测试用户{random.randint(1000, 9999)}",
        nickname=f"测试{random.randint(1000, 9999)}",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest.mark.asyncio
async def test_create_work_record_with_post(db_session: AsyncSession):
    """Test creating work record auto-creates linked post"""
    service = WorkRecordService(db_session)

    # Create test user first
    user = await create_test_user(db_session)

    work_data = WorkRecordCreate(
        clock_in_time=datetime(2025, 2, 24, 9, 0),
        work_type="overtime",
        content="加班赶项目",
        mood="tired",
        tags=["加班"]
    )

    work_record = await service.create_work_record(
        user_id=user.id,
        work_data=work_data
    )

    assert work_record.id is not None
    assert work_record.post_id is not None
    assert work_record.work_type == "overtime"

    # Verify linked post was created
    post_result = await db_session.execute(
        select(Post).where(Post.id == work_record.post_id)
    )
    post = post_result.scalar_one_or_none()

    assert post is not None
    assert post.type == "work"
    assert post.content == "加班赶项目"

@pytest.mark.asyncio
async def test_calculate_overtime_hours(db_session: AsyncSession):
    """Test overtime hours calculation"""
    service = WorkRecordService(db_session)

    # Create test user first
    user = await create_test_user(db_session)

    # Overtime on weekday
    work_data = WorkRecordCreate(
        clock_in_time=datetime(2025, 2, 24, 18, 0),  # 6 PM (weekday)
        clock_out_time=datetime(2025, 2, 24, 21, 0),  # 9 PM
        work_type="overtime",
        content="加班"
    )

    work_record = await service.create_work_record(
        user_id=user.id,
        work_data=work_data
    )

    assert work_record.overtime_hours == 3.0

@pytest.mark.asyncio
async def test_clock_out_updates_duration(db_session: AsyncSession):
    """Test clocking out updates work duration"""
    service = WorkRecordService(db_session)

    # Create test user first
    user = await create_test_user(db_session)

    # Create work record without clock out
    work_data = WorkRecordCreate(
        clock_in_time=datetime(2025, 2, 24, 9, 0),
        work_type="regular",
        content="上班"
    )

    work_record = await service.create_work_record(
        user_id=user.id,
        work_data=work_data
    )

    assert work_record.work_duration_minutes is None

    # Clock out
    await service.clock_out(
        work_record_id=work_record.id,
        clock_out_time=datetime(2025, 2, 24, 18, 0)
    )

    await db_session.refresh(work_record)
    assert work_record.work_duration_minutes == 540  # 9 hours
    assert work_record.clock_out_time is not None
