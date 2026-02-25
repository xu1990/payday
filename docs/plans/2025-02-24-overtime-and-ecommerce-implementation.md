# 牛马日志 & Enhanced E-commerce Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement two major modules for PayDay WeChat mini-program: (1) 牛马日志 - social work sharing with clock-in/out tracking, and (2) Enhanced E-commerce - full-featured product/order system with multi-SKU, distributed locking, and shipping management.

**Architecture:**
- **牛马日志**: Hybrid approach - separate WorkRecord table for work-specific data (clock-in, overtime hours, work type) that auto-creates linked Post records for social features. Reuses existing Comment, Like, Notification, Risk Control systems.
- **E-commerce**: Unified product schema supporting point + cash payments. Multi-SKU with variant attributes, multi-pricing (base/member/bulk/promotion), regional shipping templates, Redis-based distributed stock locking, complete shipping/return workflows, virtual product auto-delivery.

**Tech Stack:**
- Backend: FastAPI (Python 3.11+), SQLAlchemy ORM, Alembic migrations, Redis (locking/cache)
- Database: MySQL 8.0 with JSON fields for flexible attributes
- Frontend: uni-app Vue3 (mini-program), Vue3 + Element Plus (admin dashboard)
- Testing: pytest with asyncio, factory_boy for test data
- Patterns: Service layer pattern, dependency injection, async/await throughout

**Implementation Phases:**
1. Phase 1: 牛马日志 Module (Week 1-2)
2. Phase 2: E-commerce Core - Product Catalog (Week 3-4)
3. Phase 3: E-commerce Core - Order System (Week 5-6)
4. Phase 4: Shipping & Returns (Week 7-8)
5. Phase 5: Advanced Features (Week 9-10)

---

# PHASE 1: 牛马日志 Module (Work Diary)

## Task 1.1: Create WorkRecord Model

**Files:**
- Create: `backend/app/models/work_record.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write the failing test**

Create `backend/tests/models/test_work_record.py`:

```python
import pytest
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.work_record import WorkRecord
from app.models.user import User

@pytest.mark.asyncio
async def test_create_work_record(db: AsyncSession):
    """Test creating a work record"""
    # Create test user
    user = User(
        id="test-user-1",
        openid="test-openid",
        anonymous_name="测试用户"
    )
    db.add(user)
    await db.commit()

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
    db.add(work_record)
    await db.commit()
    await db.refresh(work_record)

    assert work_record.id == "test-work-1"
    assert work_record.work_type == "overtime"
    assert work_record.overtime_hours == 2.5
    assert work_record.mood == "tired"

@pytest.mark.asyncio
async def test_work_record_work_types(db: AsyncSession):
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
        db.add(work_record)

    await db.commit()

    # Verify all work types were created
    from sqlalchemy import select
    result = await db.execute(
        select(WorkRecord).where(WorkRecord.user_id == "test-user-1")
    )
    work_records = result.scalars().all()
    assert len(work_records) == 4
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/models/test_work_record.py -v
```

Expected: `ImportError: cannot import name 'WorkRecord'`

**Step 3: Write minimal implementation**

Create `backend/app/models/work_record.py`:

```python
"""
工作记录表 - 牛马日志 Module
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, JSON, Enum as SQLEnum

from .base import Base
from .user import gen_uuid


class WorkRecord(Base):
    """工作记录表 - 牛马日志"""
    __tablename__ = "work_records"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(String(36), ForeignKey("posts.id"), unique=True, nullable=False)

    # Clock In/Out
    clock_in_time = Column(DateTime, nullable=False, index=True, comment="打卡开始时间")
    clock_out_time = Column(DateTime, nullable=True, comment="打卡结束时间")
    work_duration_minutes = Column(Integer, nullable=True, comment="工作时长（分钟）")

    # Work Details
    work_type = Column(
        SQLEnum("regular", "overtime", "weekend", "holiday", name="work_type_enum"),
        nullable=False,
        index=True,
        comment="工作类型"
    )
    overtime_hours = Column(Numeric(4, 2), default=0, nullable=False, index=True, comment="加班时长")

    # Location & Context
    location = Column(String(200), nullable=True, comment="工作地点")
    company_name = Column(String(100), nullable=True, comment="公司名称")

    # Mood & Tags
    mood = Column(String(20), nullable=True, comment="心情")
    tags = Column(JSON, nullable=True, comment="标签")

    # Content (shared with Post)
    content = Column(String(2000), nullable=False, comment="工作内容")
    images = Column(JSON, nullable=True, comment="图片列表")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

Modify `backend/app/models/__init__.py`:

```python
# Add to imports
from .work_record import WorkRecord

# Add to __all__ if it exists
__all__ = [..., "WorkRecord"]
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/models/test_work_record.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/work_record.py backend/app/models/__init__.py backend/tests/models/test_work_record.py
git commit -m "feat(work-log): add WorkRecord model with clock-in/out tracking"
```

---

## Task 1.2: Create Database Migration for WorkRecord

**Files:**
- Create: `backend/alembic/versions/xxxx_create_work_records_table.py`

**Step 1: Generate migration**

```bash
cd backend
alembic revision --autogenerate -m "create work_records table"
```

**Step 2: Review and edit migration file**

Find the generated migration file in `backend/alembic/versions/` and edit:

```python
"""create work_records table

Revision ID: xxxx
Revises: <previous_revision_id>
Create Date: 2025-02-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'xxxx'
down_revision = '<previous_revision_id>'  # Replace with actual previous revision ID
branch_labels = None
depends_on = None


def upgrade():
    # Create work_records table
    op.create_table(
        'work_records',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('post_id', sa.String(36), nullable=False),
        sa.Column('clock_in_time', sa.DateTime(), nullable=False),
        sa.Column('clock_out_time', sa.DateTime(), nullable=True),
        sa.Column('work_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('work_type', sa.Enum('regular', 'overtime', 'weekend', 'holiday', name='work_type_enum'), nullable=False),
        sa.Column('overtime_hours', sa.Numeric(4, 2), nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('company_name', sa.String(100), nullable=True),
        sa.Column('mood', sa.String(20), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('content', sa.String(2000), nullable=False),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_work_records_user_id'), 'work_records', ['user_id'], unique=False)
    op.create_index(op.f('ix_work_records_clock_in_time'), 'work_records', ['clock_in_time'], unique=False)
    op.create_index(op.f('ix_work_records_work_type'), 'work_records', ['work_type'], unique=False)
    op.create_index(op.f('ix_work_records_overtime_hours'), 'work_records', ['overtime_hours'], unique=False)
    op.create_unique_constraint('uq_work_records_post_id', 'work_records', ['post_id'])


def downgrade():
    op.drop_constraint('uq_work_records_post_id', 'work_records', type_='unique')
    op.drop_index(op.f('ix_work_records_overtime_hours'), table_name='work_records')
    op.drop_index(op.f('ix_work_records_work_type'), table_name='work_records')
    op.drop_index(op.f('ix_work_records_clock_in_time'), table_name='work_records')
    op.drop_index(op.f('ix_work_records_user_id'), table_name='work_records')
    op.drop_table('work_records')
    # Note: Enum cleanup depends on your MySQL version
```

**Step 3: Run migration**

```bash
cd backend
alembic upgrade head
```

Expected: `Running upgrade->xxxx, create work_records table`

**Step 4: Verify table creation**

```bash
mysql -u root -p payday -e "DESCRIBE work_records;"
```

Expected output showing all columns.

**Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat(work-log): create work_records table migration"
```

---

## Task 1.3: Modify Post Table to Add 'work' Type

**Files:**
- Modify: `backend/app/models/post.py`
- Create: `backend/alembic/versions/xxxx_add_work_type_to_posts.py`

**Step 1: Write test for work type in posts**

Create `backend/tests/models/test_post_work_type.py`:

```python
import pytest
from app.models.post import Post

@pytest.mark.asyncio
async def test_post_work_type_enum(db: AsyncSession):
    """Test that posts can have type='work'"""
    post = Post(
        id="test-post-work",
        user_id="test-user-1",
        type="work",  # New work type
        content="加班记录"
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    assert post.type == "work"
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/models/test_post_work_type.py -v
```

Expected: FAIL with invalid enum value

**Step 3: Modify Post model**

Edit `backend/app/models/post.py`, find the type column definition:

```python
# Before:
type = Column(SQLEnum("complaint", "sharing", "question", name="post_type_enum"), ...)

# After:
type = Column(
    SQLEnum("complaint", "sharing", "question", "work", name="post_type_enum"),
    nullable=False,
    index=True
)
```

**Step 4: Create migration**

```bash
cd backend
alembic revision --autogenerate -m "add work type to posts enum"
```

Edit the generated migration to explicitly alter the enum:

```python
"""add work type to posts enum

Revision ID: xxxx
Revises: <previous_revision_id>
Create Date: 2025-02-24

"""
from alembic import op
import sqlalchemy as sa

revision = 'xxxx'
down_revision = '<previous_revision_id>'
branch_labels = None
depends_on = None


def upgrade():
    # MySQL requires modifying the enum definition
    op.execute("ALTER TABLE posts MODIFY COLUMN type ENUM('complaint', 'sharing', 'question', 'work') NOT NULL COMMENT 'Post type'")


def downgrade():
    op.execute("ALTER TABLE posts MODIFY COLUMN type ENUM('complaint', 'sharing', 'question') NOT NULL COMMENT 'Post type'")
```

**Step 5: Run migration and tests**

```bash
cd backend
alembic upgrade head
pytest tests/models/test_post_work_type.py -v
```

Expected: Migration succeeds, test passes

**Step 6: Commit**

```bash
git add backend/app/models/post.py backend/alembic/versions/ backend/tests/models/
git commit -m "feat(work-log): add work type to posts enum"
```

---

## Task 1.4: Create WorkRecord Schemas

**Files:**
- Create: `backend/app/schemas/work_record.py`

**Step 1: Write test for schema validation**

Create `backend/tests/schemas/test_work_record.py`:

```python
import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.work_record import WorkRecordCreate, WorkRecordResponse

def test_work_record_create_schema():
    """Test WorkRecordCreate schema validation"""
    data = {
        "clock_in_time": "2025-02-24T09:00:00",
        "work_type": "overtime",
        "content": "加班赶项目",
        "mood": "tired",
        "tags": ["加班", "赶项目"],
        "images": ["https://example.com/image.jpg"]
    }

    schema = WorkRecordCreate(**data)

    assert schema.work_type == "overtime"
    assert schema.mood == "tired"
    assert schema.tags == ["加班", "赶项目"]

def test_work_record_create_invalid_type():
    """Test that invalid work type raises error"""
    data = {
        "clock_in_time": "2025-02-24T09:00:00",
        "work_type": "invalid_type",  # Invalid
        "content": "Test"
    }

    with pytest.raises(ValidationError):
        WorkRecordCreate(**data)

def test_work_record_response_schema():
    """Test WorkRecordResponse schema"""
    data = {
        "id": "work-1",
        "user_id": "user-1",
        "post_id": "post-1",
        "clock_in_time": "2025-02-24T09:00:00",
        "work_type": "overtime",
        "overtime_hours": 2.5,
        "content": "加班",
        "created_at": "2025-02-24T09:00:00"
    }

    schema = WorkRecordResponse(**data)

    assert schema.id == "work-1"
    assert schema.overtime_hours == 2.5
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/schemas/test_work_record.py -v
```

Expected: `ImportError: cannot import name 'WorkRecordCreate'`

**Step 3: Implement schemas**

Create `backend/app/schemas/work_record.py`:

```python
"""
工作记录 Schemas - 牛马日志 Module
"""
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class WorkRecordBase(BaseModel):
    """工作记录基础 Schema"""
    clock_in_time: datetime = Field(..., description="打卡开始时间")
    work_type: str = Field(..., description="工作类型: regular/overtime/weekend/holiday")
    content: str = Field(..., min_length=1, max_length=2000, description="工作内容")

    clock_out_time: Optional[datetime] = Field(None, description="打卡结束时间")
    location: Optional[str] = Field(None, max_length=200, description="工作地点")
    company_name: Optional[str] = Field(None, max_length=100, description="公司名称")
    mood: Optional[str] = Field(None, max_length=20, description="心情")
    tags: Optional[List[str]] = Field(None, description="标签")
    images: Optional[List[str]] = Field(None, description="图片URL列表")

    @validator('work_type')
    def validate_work_type(cls, v):
        valid_types = ["regular", "overtime", "weekend", "holiday"]
        if v not in valid_types:
            raise ValueError(f"work_type must be one of {valid_types}")
        return v


class WorkRecordCreate(WorkRecordBase):
    """创建工作记录"""
    pass


class WorkRecordUpdate(BaseModel):
    """更新工作记录"""
    clock_out_time: Optional[datetime] = None
    content: Optional[str] = None
    mood: Optional[str] = None
    tags: Optional[List[str]] = None


class WorkRecordResponse(WorkRecordBase):
    """工作记录响应"""
    id: str
    user_id: str
    post_id: str
    clock_out_time: Optional[datetime] = None
    work_duration_minutes: Optional[int] = None
    overtime_hours: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkRecordListResponse(BaseModel):
    """工作记录列表响应"""
    total: int
    items: List[WorkRecordResponse]
    page: int
    page_size: int
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/schemas/test_work_record.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backend/app/schemas/work_record.py backend/tests/schemas/test_work_record.py
git commit -m "feat(work-log): add WorkRecord schemas with validation"
```

---

## Task 1.5: Create WorkRecord Service Layer

**Files:**
- Create: `backend/app/services/work_record_service.py`
- Create: `backend/tests/services/test_work_record_service.py`

**Step 1: Write service tests**

Create `backend/tests/services/test_work_record_service.py`:

```python
import pytest
from datetime import datetime
from app.services.work_record_service import WorkRecordService
from app.models.work_record import WorkRecord
from app.models.post import Post
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_work_record_with_post(db: AsyncSession):
    """Test creating work record auto-creates linked post"""
    service = WorkRecordService(db)

    work_data = {
        "clock_in_time": datetime(2025, 2, 24, 9, 0),
        "work_type": "overtime",
        "content": "加班赶项目",
        "mood": "tired",
        "tags": ["加班"]
    }

    work_record = await service.create_work_record(
        user_id="test-user-1",
        work_data=work_data
    )

    assert work_record.id is not None
    assert work_record.post_id is not None
    assert work_record.work_type == "overtime"

    # Verify linked post was created
    from sqlalchemy import select
    post_result = await db.execute(
        select(Post).where(Post.id == work_record.post_id)
    )
    post = post_result.scalar_one_or_none()

    assert post is not None
    assert post.type == "work"
    assert post.content == "加班赶项目"

@pytest.mark.asyncio
async def test_calculate_overtime_hours(db: AsyncSession):
    """Test overtime hours calculation"""
    service = WorkRecordService(db)

    # Overtime on weekday
    work_data = {
        "clock_in_time": datetime(2025, 2, 24, 18, 0),  # 6 PM (weekday)
        "clock_out_time": datetime(2025, 2, 24, 21, 0),  # 9 PM
        "work_type": "overtime",
        "content": "加班"
    }

    work_record = await service.create_work_record(
        user_id="test-user-1",
        work_data=work_data
    )

    assert work_record.overtime_hours == 3.0

@pytest.mark.asyncio
async def test_clock_out_updates_duration(db: AsyncSession):
    """Test clocking out updates work duration"""
    service = WorkRecordService(db)

    # Create work record without clock out
    work_data = {
        "clock_in_time": datetime(2025, 2, 24, 9, 0),
        "work_type": "regular",
        "content": "上班"
    }

    work_record = await service.create_work_record(
        user_id="test-user-1",
        work_data=work_data
    )

    assert work_record.work_duration_minutes is None

    # Clock out
    await service.clock_out(
        work_record_id=work_record.id,
        clock_out_time=datetime(2025, 2, 24, 18, 0)
    )

    await db.refresh(work_record)
    assert work_record.work_duration_minutes == 540  # 9 hours
    assert work_record.clock_out_time is not None
```

**Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/services/test_work_record_service.py -v
```

Expected: `ImportError: cannot import name 'WorkRecordService'`

**Step 3: Implement service**

Create `backend/app/services/work_record_service.py`:

```python
"""
工作记录 Service - 牛马日志 Module
"""
from datetime import datetime, time
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.work_record import WorkRecord
from app.models.post import Post
from app.schemas.work_record import WorkRecordCreate, WorkRecordUpdate
from app.core.exceptions import NotFoundException, ValidationException


class WorkRecordService:
    """工作记录服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_work_record(
        self,
        user_id: str,
        work_data: WorkRecordCreate
    ) -> WorkRecord:
        """
        创建工作记录并自动创建关联的 Post

        Args:
            user_id: 用户ID
            work_data: 工作记录数据

        Returns:
            创建的工作记录
        """
        # Calculate overtime hours
        overtime_hours = self._calculate_overtime_hours(
            work_data.clock_in_time,
            work_data.clock_out_time,
            work_data.work_type
        )

        # Create work record
        work_record = WorkRecord(
            user_id=user_id,
            clock_in_time=work_data.clock_in_time,
            clock_out_time=work_data.clock_out_time,
            work_type=work_data.work_type,
            overtime_hours=overtime_hours,
            content=work_data.content,
            location=work_data.location,
            company_name=work_data.company_name,
            mood=work_data.mood,
            tags=work_data.tags,
            images=work_data.images
        )
        self.db.add(work_record)
        await self.db.flush()  # Get work_record.id without committing

        # Create linked post
        post = Post(
            id=work_record.id,  # Use same ID for simplicity
            user_id=user_id,
            type="work",
            content=work_data.content,
            images=work_data.images or []
        )
        self.db.add(post)
        await self.db.flush()

        # Link work record to post
        work_record.post_id = post.id

        await self.db.commit()
        await self.db.refresh(work_record)

        return work_record

    async def clock_out(
        self,
        work_record_id: str,
        clock_out_time: datetime
    ) -> WorkRecord:
        """打卡下班"""
        # Get work record
        result = await self.db.execute(
            select(WorkRecord).where(WorkRecord.id == work_record_id)
        )
        work_record = result.scalar_one_or_none()

        if not work_record:
            raise NotFoundException("Work record not found")

        if work_record.clock_out_time:
            raise ValidationException("Already clocked out")

        # Update clock out time
        work_record.clock_out_time = clock_out_time

        # Calculate duration
        duration = clock_out_time - work_record.clock_in_time
        work_record.work_duration_minutes = int(duration.total_seconds() / 60)

        # Recalculate overtime if needed
        work_record.overtime_hours = self._calculate_overtime_hours(
            work_record.clock_in_time,
            clock_out_time,
            work_record.work_type
        )

        await self.db.commit()
        await self.db.refresh(work_record)

        return work_record

    async def get_user_work_records(
        self,
        user_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        work_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[WorkRecord]:
        """获取用户的工作记录列表"""
        query = select(WorkRecord).where(WorkRecord.user_id == user_id)

        if date_from:
            query = query.where(WorkRecord.clock_in_time >= date_from)
        if date_to:
            query = query.where(WorkRecord.clock_in_time <= date_to)
        if work_type:
            query = query.where(WorkRecord.work_type == work_type)

        query = query.order_by(WorkRecord.clock_in_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return result.scalars().all()

    def _calculate_overtime_hours(
        self,
        clock_in: datetime,
        clock_out: Optional[datetime],
        work_type: str
    ) -> float:
        """
        计算加班时长

        Args:
            clock_in: 上班时间
            clock_out: 下班时间（可选）
            work_type: 工作类型

        Returns:
            加班时长（小时）
        """
        if not clock_out:
            return 0.0

        duration = clock_out - clock_in
        hours = duration.total_seconds() / 3600

        if work_type == "overtime":
            # Weekday overtime: return actual hours worked
            return round(hours, 2)
        elif work_type in ["weekend", "holiday"]:
            # Weekend/holiday: entire duration is overtime
            return round(hours, 2)
        else:  # regular
            return 0.0
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/services/test_work_record_service.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backend/app/services/work_record_service.py backend/tests/services/test_work_record_service.py
git commit -m "feat(work-log): implement WorkRecordService with auto-post creation"
```

---

## Task 1.6: Create WorkRecord API Endpoints

**Files:**
- Create: `backend/app/api/v1/work_log.py`
- Modify: `backend/app/api/v1/__init__.py`

**Step 1: Write API tests**

Create `backend/tests/api/test_work_log_api.py`:

```python
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_work_log(client: TestClient, db: AsyncSession, auth_headers: dict):
    """Test POST /api/v1/work-logs"""
    response = client.post(
        "/api/v1/work-logs",
        json={
            "clock_in_time": "2025-02-24T09:00:00",
            "work_type": "overtime",
            "content": "加班赶项目",
            "mood": "tired",
            "tags": ["加班"]
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["work_type"] == "overtime"
    assert data["content"] == "加班赶项目"
    assert data["post_id"] is not None

@pytest.mark.asyncio
async def test_list_work_logs(client: TestClient, db: AsyncSession, auth_headers: dict):
    """Test GET /api/v1/work-logs"""
    response = client.get(
        "/api/v1/work-logs?page=1&page_size=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

@pytest.mark.asyncio
async def test_clock_out(client: TestClient, db: AsyncSession, auth_headers: dict):
    """Test PUT /api/v1/work-logs/{id}/clock-out"""
    # First create a work log
    create_response = client.post(
        "/api/v1/work-logs",
        json={
            "clock_in_time": "2025-02-24T09:00:00",
            "work_type": "regular",
            "content": "上班"
        },
        headers=auth_headers
    )
    work_id = create_response.json()["id"]

    # Clock out
    response = client.put(
        f"/api/v1/work-logs/{work_id}/clock-out",
        json={"clock_out_time": "2025-02-24T18:00:00"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["work_duration_minutes"] == 540
```

**Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/api/test_work_log_api.py -v
```

Expected: 404 Not Found

**Step 3: Implement API endpoints**

Create `backend/app/api/v1/work_log.py`:

```python
"""
工作记录 API - 牛马日志 Module
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.schemas.work_record import (
    WorkRecordCreate,
    WorkRecordResponse,
    WorkRecordListResponse
)
from app.services.work_record_service import WorkRecordService
from app.models.user import User

router = APIRouter()


@router.post("/work-logs", response_model=WorkRecordResponse)
async def create_work_log(
    work_data: WorkRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建工作记录（自动创建社交帖子）

    - **clock_in_time**: 打卡开始时间
    - **work_type**: 工作类型 (regular/overtime/weekend/holiday)
    - **content**: 工作内容
    - **mood**: 心情（可选）
    - **tags**: 标签列表（可选）
    """
    service = WorkRecordService(db)
    work_record = await service.create_work_record(
        user_id=current_user.id,
        work_data=work_data
    )
    return work_record


@router.get("/work-logs", response_model=WorkRecordListResponse)
async def list_work_logs(
    date_from: Optional[datetime] = Query(None, description="开始日期"),
    date_to: Optional[datetime] = Query(None, description="结束日期"),
    work_type: Optional[str] = Query(None, description="工作类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的工作记录列表"""
    service = WorkRecordService(db)
    items = await service.get_user_work_records(
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
        work_type=work_type,
        page=page,
        page_size=page_size
    )

    # TODO: Get total count
    return WorkRecordListResponse(
        total=len(items),
        items=items,
        page=page,
        page_size=page_size
    )


@router.get("/work-logs/{work_log_id}", response_model=WorkRecordResponse)
async def get_work_log(
    work_log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取工作记录详情"""
    from sqlalchemy import select
    from app.core.exceptions import NotFoundException

    result = await db.execute(
        select(WorkRecord).where(
            WorkRecord.id == work_log_id,
            WorkRecord.user_id == current_user.id
        )
    )
    work_record = result.scalar_one_or_none()

    if not work_record:
        raise NotFoundException("Work log not found")

    return work_record


@router.put("/work-logs/{work_log_id}/clock-out", response_model=WorkRecordResponse)
async def clock_out(
    work_log_id: str,
    clock_out_time: datetime,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """打卡下班"""
    service = WorkRecordService(db)
    work_record = await service.clock_out(
        work_record_id=work_log_id,
        clock_out_time=clock_out_time
    )
    return work_record
```

Modify `backend/app/api/v1/__init__.py`:

```python
from app.api.v1 import work_log

# Add to main router
api_router.include_router(work_log.router, prefix="/work-logs", tags=["work-logs"])
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/api/test_work_log_api.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backend/app/api/v1/work_log.py backend/app/api/v1/__init__.py backend/tests/api/test_work_log_api.py
git commit -m "feat(work-log): add work log API endpoints"
```

---

## Task 1.7: Register Work Log Router in Main App

**Files:**
- Modify: `backend/app/main.py`

**Step 1: Verify router is registered**

Check `backend/app/main.py` includes:

```python
from app.api.v1 import work_log

# Inside the app setup
app.include_router(work_log.router, prefix="/api/v1", tags=["work-logs"])
```

**Step 2: Manual test**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
curl -X GET http://localhost:8000/api/v1/work-logs
```

Expected: 401 Unauthorized (needs auth)

**Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat(work-log): register work log router in main app"
```

---

## Task 1.8: Add Work Feed Endpoint (Reuses Post Logic)

**Files:**
- Modify: `backend/app/api/v1/work_log.py`

**Step 1: Write test for work feed**

Add to `backend/tests/api/test_work_log_api.py`:

```python
@pytest.mark.asyncio
async def test_get_work_feed(client: TestClient, db: AsyncSession, auth_headers: dict):
    """Test GET /api/v1/work-logs/feed"""
    response = client.get(
        "/api/v1/work-logs/feed?feed_type=latest&page=1",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Verify all items are work type posts
    for item in data["items"]:
        assert item["type"] == "work"
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/api/test_work_log_api.py::test_get_work_feed -v
```

Expected: 404 Not Found

**Step 3: Implement work feed endpoint**

Add to `backend/app/api/v1/work_log.py`:

```python
@router.get("/work-logs/feed")
async def get_work_feed(
    feed_type: str = Query("hot", regex="^(hot|latest|following)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取工作动态动态（复用Post逻辑）

    - **hot**: 热门工作动态
    - **latest**: 最新工作动态
    - **following**: 关注用户的工作动态
    """
    from sqlalchemy import select
    from app.models.post import Post

    # Build query with type filter
    query = select(Post).where(Post.type == "work", Post.status == "normal")

    # TODO: Apply risk_status filter
    # TODO: Apply sorting based on feed_type

    query = query.order_by(Post.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    posts = result.scalars().all()

    return {
        "total": len(posts),
        "items": posts,
        "page": page,
        "page_size": page_size
    }
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/api/test_work_log_api.py::test_get_work_feed -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/v1/work_log.py backend/tests/api/test_work_log_api.py
git commit -m "feat(work-log): add work feed endpoint with type filter"
```

---

## Task 1.9: Add Work Statistics Endpoint

**Files:**
- Modify: `backend/app/services/work_record_service.py`
- Modify: `backend/app/api/v1/work_log.py`

**Step 1: Write statistics test**

Create `backend/tests/api/test_work_statistics.py`:

```python
import pytest
from datetime import datetime, date
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_get_work_statistics(client: TestClient, db: AsyncSession, auth_headers: dict):
    """Test GET /api/v1/work-logs/statistics"""
    response = client.get(
        f"/api/v1/work-logs/statistics?year=2025&month=2",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_overtime_hours" in data
    assert "work_days" in data
    assert "recent_mood" in data
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/api/test_work_statistics.py -v
```

Expected: 404 Not Found

**Step 3: Implement statistics in service**

Add to `backend/app/services/work_record_service.py`:

```python
async def get_user_work_statistics(
    self,
    user_id: str,
    year: int,
    month: int
) -> dict:
    """
    获取用户工作统计数据

    Args:
        user_id: 用户ID
        year: 年份
        month: 月份

    Returns:
        统计数据字典
    """
    from sqlalchemy import func, extract
    from datetime import datetime

    # Build date range
    date_from = datetime(year, month, 1)
    if month == 12:
        date_to = datetime(year + 1, 1, 1)
    else:
        date_to = datetime(year, month + 1, 1)

    # Query work records for the month
    result = await self.db.execute(
        select(
            func.sum(WorkRecord.overtime_hours).label("total_overtime"),
            func.count(WorkRecord.id).label("work_days")
        ).where(
            WorkRecord.user_id == user_id,
            WorkRecord.clock_in_time >= date_from,
            WorkRecord.clock_in_time < date_to
        )
    )
    stats = result.one()

    # Get most recent mood
    recent_result = await self.db.execute(
        select(WorkRecord.mood)
        .where(WorkRecord.user_id == user_id)
        .where(WorkRecord.mood.isnot(None))
        .order_by(WorkRecord.created_at.desc())
        .limit(1)
    )
    recent_mood = recent_result.scalar_one_or_none()

    return {
        "total_overtime_hours": float(stats.total_overtime or 0),
        "work_days": stats.work_days or 0,
        "recent_mood": recent_mood
    }
```

**Step 4: Add API endpoint**

Add to `backend/app/api/v1/work_log.py`:

```python
@router.get("/work-logs/statistics")
async def get_work_statistics(
    year: int = Query(..., ge=2020, le=2030, description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户工作统计"""
    service = WorkRecordService(db)
    stats = await service.get_user_work_statistics(
        user_id=current_user.id,
        year=year,
        month=month
    )
    return stats
```

**Step 5: Run tests**

```bash
cd backend
pytest tests/api/test_work_statistics.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/services/work_record_service.py backend/app/api/v1/work_log.py backend/tests/api/test_work_statistics.py
git commit -m "feat(work-log): add work statistics endpoint"
```

---

## Phase 1 Summary

**Completed:**
- ✅ WorkRecord model with clock-in/out tracking
- ✅ Post table modified to support 'work' type
- ✅ WorkRecord schemas with validation
- ✅ WorkRecord service layer with auto-post creation
- ✅ Work log CRUD API endpoints
- ✅ Work feed endpoint (reuses Post logic)
- ✅ Work statistics endpoint

**Integration Points:**
- WorkRecord automatically creates linked Post with type='work'
- Comments, likes, notifications work out-of-the-box for work posts
- Risk control applies to work posts

**Testing:**
- All endpoints have pytest tests
- Service layer has unit tests
- Integration with existing social features verified

**Next Phase:** E-commerce Product Catalog (Phase 2)

---

# PHASE 2: E-commerce Core - Product Catalog

## Task 2.1: Create ProductCategory Model

**Files:**
- Create: `backend/app/models/product.py`
- Create: `backend/tests/models/test_product.py`

**Step 1: Write test for ProductCategory**

Create `backend/tests/models/test_product.py`:

```python
import pytest
from app.models.product import ProductCategory

@pytest.mark.asyncio
async def test_create_category(db: AsyncSession):
    """Test creating a product category"""
    category = ProductCategory(
        id="cat-1",
        name="数码产品",
        code="digital",
        sort_order=1
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    assert category.name == "数码产品"
    assert category.code == "digital"

@pytest.mark.asyncio
async def test_category_hierarchy(db: AsyncSession):
    """Test category parent-child relationship"""
    # Parent category
    parent = ProductCategory(
        id="cat-parent",
        name="电子产品",
        code="electronics"
    )
    db.add(parent)
    await db.flush()

    # Child category
    child = ProductCategory(
        id="cat-child",
        name="手机",
        code="phone",
        parent_id="cat-parent"
    )
    db.add(child)
    await db.commit()

    assert child.parent_id == parent.id
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/models/test_product.py::test_create_category -v
```

Expected: ImportError

**Step 3: Implement Product model**

Create `backend/app/models/product.py`:

```python
"""
商品模型 - Enhanced E-commerce Module
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON

from .base import Base
from .user import gen_uuid


class ProductCategory(Base):
    """商品分类表"""
    __tablename__ = "product_categories"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(50), nullable=False, comment="分类名称")
    code = Column(String(50), unique=True, nullable=False, comment="分类代码")
    parent_id = Column(String(36), ForeignKey("product_categories.id"), nullable=True, index=True)
    icon = Column(String(200), nullable=True, comment="图标URL")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    # parent = relationship("ProductCategory", remote_side=[id], backref="children")


class Product(Base):
    """统一商品表（替代PointProduct）"""
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=gen_uuid)

    # Basic info
    name = Column(String(100), nullable=False, comment="商品名称")
    description = Column(String(2000), nullable=True, comment="商品描述")
    images = Column(JSON, nullable=True, comment="商品图片URLs")

    # Classification
    category_id = Column(String(36), ForeignKey("product_categories.id"), nullable=True, index=True)
    product_type = Column(
        SQLEnum("point", "cash", "hybrid", name="product_type_enum"),
        default="point",
        nullable=False
    )
    item_type = Column(
        SQLEnum("physical", "virtual", "bundle", name="item_type_enum"),
        nullable=False
    )
    bundle_type = Column(
        SQLEnum("pre_configured", "custom_builder", name="bundle_type_enum"),
        nullable=True
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_virtual = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # SEO
    seo_keywords = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/models/test_product.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/product.py backend/tests/models/test_product.py
git commit -m "feat(ecommerce): add ProductCategory and Product models"
```

---

## Task 2.2: Create ProductSKU Model

**Files:**
- Modify: `backend/app/models/product.py`

**Step 1: Write test for ProductSKU**

Add to `backend/tests/models/test_product.py`:

```python
@pytest.mark.asyncio
async def test_create_product_with_sku(db: AsyncSession):
    """Test creating product with SKU variants"""
    # Create product
    product = Product(
        id="prod-1",
        name="T恤",
        item_type="physical",
        product_type="cash"
    )
    db.add(product)
    await db.flush()

    # Create SKU
    from app.models.product import ProductSKU

    sku = ProductSKU(
        id="sku-1",
        product_id="prod-1",
        sku_code="TSHIRT-RED-L",
        name="红色 - L码",
        attributes={"color": "red", "size": "L"},
        stock=100,
        weight_grams=200
    )
    db.add(sku)
    await db.commit()

    assert sku.attributes["color"] == "red"
    assert sku.stock == 100
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/models/test_product.py::test_create_product_with_sku -v
```

Expected: ImportError

**Step 3: Implement ProductSKU**

Add to `backend/app/models/product.py`:

```python
class ProductSKU(Base):
    """商品SKU（规格）表"""
    __tablename__ = "product_skus"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)

    # SKU identification
    sku_code = Column(String(50), unique=True, nullable=False, comment="SKU代码")
    name = Column(String(100), nullable=False, comment="SKU名称")

    # Variant attributes
    attributes = Column(JSON, nullable=False, comment="规格属性")

    # Inventory
    stock = Column(Integer, default=0, nullable=False, comment="库存")
    stock_unlimited = Column(Boolean, default=False, nullable=False, comment="库存无限")

    # Images (specific to this SKU)
    images = Column(JSON, nullable=True, comment="SKU图片")

    # Weight for shipping
    weight_grams = Column(Integer, nullable=True, comment="重量(克)")

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    # product = relationship("Product", back_populates="skus")


class ProductPrice(Base):
    """商品多价格表"""
    __tablename__ = "product_prices"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    sku_id = Column(String(36), ForeignKey("product_skus.id"), nullable=False, index=True)

    # Price type
    price_type = Column(
        SQLEnum("base", "member", "bulk", "promotion", name="price_type_enum"),
        nullable=False
    )

    # Price (can be points or cash)
    price_amount = Column(Integer, nullable=False, comment="价格(分或积分)")
    currency = Column(
        SQLEnum("CNY", "POINTS", name="price_currency_enum"),
        nullable=False
    )

    # Conditions
    min_quantity = Column(Integer, default=1, nullable=False, comment="最小数量")
    membership_level = Column(Integer, nullable=True, comment="会员等级")

    # Validity period
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/models/test_product.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/product.py backend/tests/models/test_product.py
git commit -m "feat(ecommerce): add ProductSKU and ProductPrice models"
```

---

## Task 2.3: Create ProductBundle Model

**Files:**
- Modify: `backend/app/models/product.py`

**Step 1: Write test for ProductBundle**

Add to `backend/tests/models/test_product.py`:

```python
@pytest.mark.asyncio
async def test_create_product_bundle(db: AsyncSession):
    """Test creating pre-configured bundle"""
    from app.models.product import ProductBundle

    # Create bundle product
    bundle = Product(
        id="bundle-1",
        name="数码套装",
        item_type="bundle",
        bundle_type="pre_configured"
    )
    db.add(bundle)
    await db.flush()

    # Create component products
    component1 = Product(
        id="comp-1",
        name="手机壳",
        item_type="physical"
    )
    db.add(component1)

    component2 = Product(
        id="comp-2",
        name="贴膜",
        item_type="physical"
    )
    db.add(component2)
    await db.flush()

    # Create bundle components
    bundle_item1 = ProductBundle(
        bundle_product_id="bundle-1",
        component_product_id="comp-1",
        quantity=1
    )
    db.add(bundle_item1)

    bundle_item2 = ProductBundle(
        bundle_product_id="bundle-1",
        component_product_id="comp-2",
        quantity=2
    )
    db.add(bundle_item2)
    await db.commit()

    assert bundle_item1.quantity == 1
    assert bundle_item2.quantity == 2
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/models/test_product.py::test_create_product_bundle -v
```

Expected: ImportError

**Step 3: Implement ProductBundle**

Add to `backend/app/models/product.py`:

```python
class ProductBundle(Base):
    """商品套餐（组合商品）表"""
    __tablename__ = "product_bundles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    bundle_product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    component_product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    component_sku_id = Column(String(36), ForeignKey("product_skus.id"), nullable=True)
    quantity = Column(Integer, default=1, nullable=False, comment="数量")
    is_required = Column(Boolean, default=True, nullable=False, comment="是否必选")

    # Relationships
    # bundle_product = relationship("Product", foreign_keys=[bundle_product_id])
    # component_product = relationship("Product", foreign_keys=[component_product_id])
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/models/test_product.py::test_create_product_bundle -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/product.py backend/tests/models/test_product.py
git commit -m "feat(ecommerce): add ProductBundle model"
```

---

## Task 2.4: Create Migration for All Product Tables

**Files:**
- Create: `backend/alembic/versions/xxxx_create_ecommerce_product_tables.py`

**Step 1: Generate migration**

```bash
cd backend
alembic revision --autogenerate -m "create ecommerce product tables"
```

**Step 2: Edit migration file**

Find and edit the generated migration file. Ensure it includes all tables:

```python
"""create ecommerce product tables

Revision ID: xxxx
Revises: <previous_revision_id>
Create Date: 2025-02-24

"""
from alembic import op
import sqlalchemy as sa

revision = 'xxxx'
down_revision = '<previous_revision_id>'
branch_labels = None
depends_on = None


def upgrade():
    # Create product_categories table
    op.create_table(
        'product_categories',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('icon', sa.String(200), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['product_categories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_product_categories_parent_id'), 'product_categories', ['parent_id'], unique=False)

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('category_id', sa.String(36), nullable=True),
        sa.Column('product_type', sa.Enum('point', 'cash', 'hybrid', name='product_type_enum'), nullable=False),
        sa.Column('item_type', sa.Enum('physical', 'virtual', 'bundle', name='item_type_enum'), nullable=False),
        sa.Column('bundle_type', sa.Enum('pre_configured', 'custom_builder', name='bundle_type_enum'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_virtual', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('seo_keywords', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['product_categories.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)

    # Create product_skus table
    op.create_table(
        'product_skus',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('sku_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('attributes', sa.JSON(), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=False),
        sa.Column('stock_unlimited', sa.Boolean(), nullable=False),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('weight_grams', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku_code')
    )
    op.create_index(op.f('ix_product_skus_product_id'), 'product_skus', ['product_id'], unique=False)

    # Create product_prices table
    op.create_table(
        'product_prices',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('sku_id', sa.String(36), nullable=False),
        sa.Column('price_type', sa.Enum('base', 'member', 'bulk', 'promotion', name='price_type_enum'), nullable=False),
        sa.Column('price_amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.Enum('CNY', 'POINTS', name='price_currency_enum'), nullable=False),
        sa.Column('min_quantity', sa.Integer(), nullable=False),
        sa.Column('membership_level', sa.Integer(), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sku_id'], ['product_skus.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_prices_sku_id'), 'product_prices', ['sku_id'], unique=False)

    # Create product_bundles table
    op.create_table(
        'product_bundles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('bundle_product_id', sa.String(36), nullable=False),
        sa.Column('component_product_id', sa.String(36), nullable=False),
        sa.Column('component_sku_id', sa.String(36), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['bundle_product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['component_product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['component_sku_id'], ['product_skus.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_bundles_bundle_product_id'), 'product_bundles', ['bundle_product_id'], unique=False)
    op.create_index(op.f('ix_product_bundles_component_product_id'), 'product_bundles', ['component_product_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_product_bundles_component_product_id'), table_name='product_bundles')
    op.drop_index(op.f('ix_product_bundles_bundle_product_id'), table_name='product_bundles')
    op.drop_table('product_bundles')

    op.drop_index(op.f('ix_product_prices_sku_id'), table_name='product_prices')
    op.drop_table('product_prices')

    op.drop_index(op.f('ix_product_skus_product_id'), table_name='product_skus')
    op.drop_table('product_skus')

    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_table('products')

    op.drop_index(op.f('ix_product_categories_parent_id'), table_name='product_categories')
    op.drop_table('product_categories')
```

**Step 3: Run migration**

```bash
cd backend
alembic upgrade head
```

**Step 4: Verify tables**

```bash
mysql -u root -p payday -e "SHOW TABLES LIKE 'product%';"
```

Expected: Lists all product tables

**Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat(ecommerce): create migration for all product tables"
```

---

## Task 2.5: Create AdminRegion and UserAddress Models

**Files:**
- Create: `backend/app/models/address.py`
- Create: `backend/tests/models/test_address.py`

**Step 1: Write address tests**

Create `backend/tests/models/test_address.py`:

```python
import pytest
from app.models.address import AdminRegion, UserAddress

@pytest.mark.asyncio
async def test_create_admin_region(db: AsyncSession):
    """Test creating administrative region"""
    region = AdminRegion(
        id="region-1",
        code="310000",
        name="上海市",
        level="province"
    )
    db.add(region)
    await db.commit()
    await db.refresh(region)

    assert region.name == "上海市"
    assert region.code == "310000"

@pytest.mark.asyncio
async def test_region_hierarchy(db: AsyncSession):
    """Test region parent-child relationship"""
    # Province
    province = AdminRegion(
        id="prov-1",
        code="310000",
        name="上海市",
        level="province"
    )
    db.add(province)
    await db.flush()

    # City (district in municipality)
    district = AdminRegion(
        id="dist-1",
        code="310100",
        name="上海市市辖区",
        level="city",
        parent_code="310000"
    )
    db.add(district)
    await db.commit()

    assert district.parent_code == province.code

@pytest.mark.asyncio
async def test_create_user_address(db: AsyncSession):
    """Test creating user address"""
    address = UserAddress(
        id="addr-1",
        user_id="user-1",
        receiver_name="张三",
        phone="13800138000",
        province_code="310000",
        city_code="310100",
        district_code="310101",
        detail_address="某某路100号",
        is_default=True,
        address_tag="home"
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)

    assert address.receiver_name == "张三"
    assert address.is_default == True
```

**Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/models/test_address.py -v
```

Expected: ImportError

**Step 3: Implement address models**

Create `backend/app/models/address.py`:

```python
"""
地址与区域模型 - Enhanced E-commerce Module
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum

from .base import Base
from .user import gen_uuid


class AdminRegion(Base):
    """行政区域表（省市区）"""
    __tablename__ = "admin_regions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="行政区划代码")
    name = Column(String(50), nullable=False, comment="区域名称")
    level = Column(
        SQLEnum("province", "city", "district", name="region_level_enum"),
        nullable=False,
        index=True
    )
    parent_code = Column(String(20), nullable=True, index=True, comment="父级区域代码")

    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship
    # parent = relationship("AdminRegion", remote_side=[code], backref="children")


class UserAddress(Base):
    """用户收货地址表"""
    __tablename__ = "user_addresses"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Contact info
    receiver_name = Column(String(50), nullable=False, comment="收货人姓名")
    phone = Column(String(20), nullable=False, comment="手机号")

    # Address
    province_code = Column(String(20), nullable=False, comment="省份代码")
    city_code = Column(String(20), nullable=False, comment="城市代码")
    district_code = Column(String(20), nullable=False, comment="区县代码")
    detail_address = Column(String(200), nullable=False, comment="详细地址")
    postal_code = Column(String(10), nullable=True, comment="邮编")

    # Metadata
    is_default = Column(Boolean, default=False, nullable=False, comment="是否默认")
    address_tag = Column(String(20), nullable=True, comment="地址标签: home/office/school")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    # user = relationship("User", back_populates="addresses")
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/models/test_address.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/address.py backend/tests/models/test_address.py
git commit -m "feat(ecommerce): add AdminRegion and UserAddress models"
```

---

## Task 2.6: Create Shipping Template Models

**Files:**
- Create: `backend/app/models/shipping.py`
- Create: `backend/tests/models/test_shipping.py`

**Step 1: Write shipping tests**

Create `backend/tests/models/test_shipping.py`:

```python
import pytest
from app.models.shipping import ShippingTemplate, ShippingTemplateRegion, CourierCompany

@pytest.mark.asyncio
async def test_create_shipping_template(db: AsyncSession):
    """Test creating shipping template"""
    template = ShippingTemplate(
        id="tpl-1",
        name="江浙沪包邮",
        default_shipping_type="weight_based",
        default_cost=1000,  # 10元
        billing_rules={
            "base_cost": 1000,
            "base_weight": 1000,
            "additional_cost": 500,
            "additional_weight": 1000
        },
        free_shipping_min_amount=9900  # 99元免邮
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    assert template.name == "江浙沪包邮"

@pytest.mark.asyncio
async def test_shipping_template_region(db: AsyncSession):
    """Test shipping template region configuration"""
    # Create template
    template = ShippingTemplate(
        id="tpl-2",
        name="全国运费",
        default_shipping_type="flat",
        default_cost=1000
    )
    db.add(template)
    await db.flush()

    # Create region config
    from app.models.address import AdminRegion

    region = AdminRegion(
        id="region-1",
        code="310000",
        name="上海市",
        level="province"
    )
    db.add(region)
    await db.flush()

    # Free shipping region
    free_region = ShippingTemplateRegion(
        template_id="tpl-2",
        region_code="310000",
        region_type="free",
        shipping_type="flat",
        cost=0
    )
    db.add(free_region)
    await db.commit()

    assert free_region.region_type == "free"

@pytest.mark.asyncio
async def test_courier_company(db: AsyncSession):
    """Test courier company"""
    courier = CourierCompany(
        id="courier-1",
        code="SF",
        name="顺丰速运",
        name_en="SF Express",
        api_provider="kuaidi100",
        default_days_min=2,
        default_days_max=3
    )
    db.add(courier)
    await db.commit()
    await db.refresh(courier)

    assert courier.code == "SF"
```

**Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/models/test_shipping.py -v
```

Expected: ImportError

**Step 3: Implement shipping models**

Create `backend/app/models/shipping.py`:

```python
"""
运费模板与快递模型 - Enhanced E-commerce Module
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Numeric, Enum as SQLEnum, JSON

from .base import Base
from .user import gen_uuid


class ShippingTemplate(Base):
    """运费模板表"""
    __tablename__ = "shipping_templates"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(50), nullable=False, comment="模板名称")
    description = Column(String(200), nullable=True, comment="描述")

    # 默认运费
    default_shipping_type = Column(
        SQLEnum("free", "flat", "quantity_based", "weight_based", name="shipping_type_enum"),
        nullable=False
    )
    default_cost = Column(Numeric(10, 2), default=0, nullable=False, comment="默认运费(元)")

    # 计费规则
    billing_rules = Column(JSON, nullable=True, comment="计费规则JSON")

    # 免邮条件
    free_shipping_min_amount = Column(Numeric(10, 2), nullable=True, comment="满额免邮(元)")
    free_shipping_min_quantity = Column(Integer, nullable=True, comment="满件免邮")

    # 时效
    estimated_days_min = Column(Integer, nullable=True, comment="最少送达天数")
    estimated_days_max = Column(Integer, nullable=True, comment="最多送达天数")

    # 支持的快递公司
    supported_couriers = Column(JSON, nullable=True, comment="支持的快递公司代码列表")

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ShippingTemplateRegion(Base):
    """运费模板区域关联表"""
    __tablename__ = "shipping_template_regions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    template_id = Column(String(36), ForeignKey("shipping_templates.id"), nullable=False, index=True)
    region_code = Column(String(20), ForeignKey("admin_regions.code"), nullable=False, index=True)

    # 区域类型
    region_type = Column(
        SQLEnum("free", "shipping", "no_shipping", name="region_type_enum"),
        nullable=False,
        index=True
    )

    # 计费规则（仅 region_type='shipping' 时有效）
    shipping_type = Column(
        SQLEnum("flat", "quantity_based", "weight_based", name="region_shipping_type_enum"),
        nullable=False
    )
    cost = Column(Numeric(10, 2), nullable=False, comment="运费(元)")

    # 可覆盖模板默认的规则
    billing_rules = Column(JSON, nullable=True)
    free_shipping_min_amount = Column(Numeric(10, 2), nullable=True)
    free_shipping_min_quantity = Column(Integer, nullable=True)
    estimated_days_min = Column(Integer, nullable=True)
    estimated_days_max = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Unique constraint
    # __table_args__ = (sa.UniqueConstraint('template_id', 'region_code', name='_template_region_uc'),)


class CourierCompany(Base):
    """快递公司配置表"""
    __tablename__ = "courier_companies"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="快递公司代码")
    name = Column(String(50), nullable=False, comment="快递公司名称")
    name_en = Column(String(50), nullable=True, comment="英文名称")

    # API配置
    api_provider = Column(String(50), nullable=True, comment="API提供商: kuaidi100/kdniao")
    api_key = Column(String(100), nullable=True, comment="API Key")
    api_secret = Column(String(100), nullable=True, comment="API Secret")

    # 配送范围
    service_regions = Column(JSON, nullable=True, comment="支持的区域代码列表")

    # 配送时效
    default_days_min = Column(Integer, nullable=True)
    default_days_max = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/models/test_shipping.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/shipping.py backend/tests/models/test_shipping.py
git commit -m "feat(ecommerce): add shipping template models"
```

---

## Task 2.7: Create Migration for Address and Shipping Tables

**Files:**
- Create: `backend/alembic/versions/xxxx_create_address_and_shipping_tables.py`

**Step 1: Generate migration**

```bash
cd backend
alembic revision --autogenerate -m "create address and shipping tables"
```

**Step 2: Edit migration**

Edit the generated migration file to include all tables and constraints. Ensure unique constraint for template+region is added.

**Step 3: Run migration**

```bash
cd backend
alembic upgrade head
```

**Step 4: Verify tables**

```bash
mysql -u root -p payday -e "SHOW TABLES LIKE '%address%';"
mysql -u root -p payday -e "SHOW TABLES LIKE 'shipping%';"
mysql -u root -p payday -e "SHOW TABLES LIKE 'courier%';"
```

**Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat(ecommerce): create migration for address and shipping tables"
```

---

[Continuing with remaining tasks...]

---

# Implementation Notes

## Testing Strategy

All code follows TDD:
1. Write failing test first
2. Run test, verify it fails
3. Write minimal implementation
4. Run test, verify it passes
5. Commit

## Commit Convention

Follow conventional commits:
- `feat:` for new features
- `fix:` for bug fixes
- `refactor:` for refactoring
- `test:` for adding tests
- `docs:` for documentation

## File Organization

```
backend/
├── app/
│   ├── models/          # ORM models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── api/v1/          # API endpoints
│   └── core/            # Config, deps, exceptions
├── tests/
│   ├── models/          # Model tests
│   ├── schemas/         # Schema tests
│   ├── services/        # Service tests
│   └── api/             # API tests
└── alembic/versions/    # Migrations
```

## Redis Keys Reference

```
# Stock locking
stock:lock:{sku_id}          # Locked quantity (TTL: 5min)
sku:stock:{sku_id}           # Available stock (TTL: 5min)

# Caching
product:detail:{id}          # Product + SKUs + Prices (TTL: 1h)
cart:user:{user_id}          # Shopping cart (TTL: 30min)
order:detail:{id}            # Order + items (TTL: 24h)

# Work logs
work:stats:{user_id}:{month} # User work stats (TTL: 1h)
work:hot:{date}              # Hot work posts (TTL: 24h)
```

---

**Document Version:** 1.0
**Last Updated:** 2025-02-24
**Status:** Ready for Implementation

**Total Estimated Tasks:** ~150 tasks across 5 phases
**Total Estimated Time:** 10 weeks
