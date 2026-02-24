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
        # Get user info for post
        from app.models.user import User
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")

        # Calculate overtime hours
        overtime_hours = self._calculate_overtime_hours(
            work_data.clock_in_time,
            work_data.clock_out_time,
            work_data.work_type
        )

        # Generate ID for both records
        import uuid
        record_id = str(uuid.uuid4())

        # Create linked post first
        post = Post(
            id=record_id,
            user_id=user_id,
            anonymous_name=user.anonymous_name,
            user_avatar=user.avatar,
            type="work",
            content=work_data.content,
            images=work_data.images or []
        )
        self.db.add(post)
        await self.db.flush()

        # Create work record with post_id
        work_record = WorkRecord(
            id=record_id,
            user_id=user_id,
            post_id=post.id,  # Link to post
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
