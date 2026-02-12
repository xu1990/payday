"""
发薪日配置 - 增删改查
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payday import PaydayConfig
from app.schemas.payday import PaydayConfigCreate, PaydayConfigUpdate


async def list_by_user(db: AsyncSession, user_id: str) -> List[PaydayConfig]:
    result = await db.execute(
        select(PaydayConfig).where(PaydayConfig.user_id == user_id).order_by(PaydayConfig.created_at)
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, config_id: str, user_id: str) -> Optional[PaydayConfig]:
    result = await db.execute(
        select(PaydayConfig).where(PaydayConfig.id == config_id, PaydayConfig.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user_id: str, data: PaydayConfigCreate) -> PaydayConfig:
    config = PaydayConfig(
        user_id=user_id,
        job_name=data.job_name,
        payday=data.payday,
        calendar_type=data.calendar_type,
        estimated_salary=data.estimated_salary,
        is_active=data.is_active,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


async def update(
    db: AsyncSession, config_id: str, user_id: str, data: PaydayConfigUpdate
) -> Optional[PaydayConfig]:
    config = await get_by_id(db, config_id, user_id)
    if not config:
        return None
    d = data.model_dump(exclude_unset=True)
    for k, v in d.items():
        setattr(config, k, v)
    await db.commit()
    await db.refresh(config)
    return config


async def delete(db: AsyncSession, config_id: str, user_id: str) -> bool:
    config = await get_by_id(db, config_id, user_id)
    if not config:
        return False
    await db.delete(config)
    await db.commit()
    return True
