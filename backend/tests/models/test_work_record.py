import pytest
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.work_record import WorkRecord
from app.models.user import User

@pytest.mark.asyncio
async def test_create_work_record(db_session: AsyncSession):
    """Test creating a work record"""
    # Create test user
    user = User(
        id="test-user-1",
        openid="test-openid",
        anonymous_name="测试用户"
    )
    db_session.add(user)
    await db_session.commit()

    # Create work record
    work_record = WorkRecord(
        id="test-work-1",
        user_id="test-user-1",
        post_id="test-post-1",  # Will be linked later
        clock_in_time=datetime(2025, 2, 24, 9, 0),
        work_type="overtime",
        overtime_hours=2.5,
        mood="tired",
        content="加班赶项目"
    )
    db_session.add(work_record)
    await db_session.commit()
    await db_session.refresh(work_record)

    assert work_record.id == "test-work-1"
    assert work_record.work_type == "overtime"
    assert work_record.overtime_hours == 2.5
    assert work_record.mood == "tired"

@pytest.mark.asyncio
async def test_work_record_work_types(db_session: AsyncSession):
    """Test all valid work types"""
    valid_types = ["regular", "overtime", "weekend", "holiday"]

    for work_type in valid_types:
        work_record = WorkRecord(
            id=f"test-work-{work_type}",
            user_id="test-user-1",
            post_id=f"test-post-{work_type}",
            clock_in_time=datetime.now(),
            work_type=work_type,
            content="Test"
        )
        db_session.add(work_record)

    await db_session.commit()

    # Verify all work types were created
    from sqlalchemy import select
    result = await db_session.execute(
        select(WorkRecord).where(WorkRecord.user_id == "test-user-1")
    )
    work_records = result.scalars().all()
    assert len(work_records) == 4
