"""
分享服务 - P1-2 分享功能
提供分享记录的创建、查询、状态更新等功能
"""
from typing import List, Literal, Optional
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.share import Share
from app.schemas.share import ShareCreate, ShareResponse
from app.core.exceptions import NotFoundException


async def create_share(
    db: AsyncSession,
    user_id: str,
    target_type: str,
    target_id: str,
    share_channel: str,
) -> Share:
    """创建分享记录"""
    share = Share(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        share_channel=share_channel,
        share_status="pending",
    )
    db.add(share)
    await db.commit()
    await db.refresh(share)
    return share


async def update_share_status(
    db: AsyncSession,
    share_id: str,
    status: Literal["success", "failed"],
    error_message: Optional[str] = None,
) -> Optional[Share]:
    """更新分享状态（成功/失败）"""
    result = await db.execute(
        select(Share).where(Share.id == share_id)
    )
    share = result.scalar_one_or_none()
    if not share:
        raise NotFoundException("分享记录不存在")

    share.share_status = status
    if status == "failed" and error_message:
        share.error_message = error_message
    share.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(share)
    return share


async def get_user_shares(
    db: AsyncSession,
    user_id: str,
    target_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[List[Share], int]:
    """获取用户的分享记录"""
    # 构建基础查询
    query = select(Share).where(Share.user_id == user_id)

    # 按类型筛选
    if target_type:
        query = query.where(Share.target_type == target_type)

    # 按时间倒序查询
    query = query.order_by(Share.created_at.desc())

    # 获取总数
    from sqlalchemy import func as sqlalchemy_func
    count_query = select(sqlalchemy_func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 应用分页
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    shares = result.scalars().all()

    return list(shares), total


async def get_share_stats(
    db: AsyncSession,
    user_id: str,
    days: int = 7,
) -> dict:
    """获取用户分享统计（最近N天的分享次数、成功率）"""
    # 修复：使用 UTC 时间以保持与代码库其他部分一致
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # 查询最近N天的分享记录
    result = await db.execute(
        select(Share).where(
            and_(
                Share.user_id == user_id,
                Share.created_at >= since
            )
        )
    )

    # 获取Share对象列表
    all_shares = result.scalars().all()
    total_shares = len(all_shares)
    success_shares = len([s for s in all_shares if s.share_status == "success"])
    success_rate = (success_shares / total_shares * 100) if total_shares > 0 else 0

    return {
        "total_shares": total_shares,
        "success_shares": success_shares,
        "success_rate": f"{success_rate:.1f}%",
        "days": days
    }
