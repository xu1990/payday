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
