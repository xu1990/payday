"""
发帖后异步风控检查：取帖子 → 文本/图片评分 → 更新 risk_status/risk_score/risk_reason；拒绝则下架并发系统通知
使用 Celery 异步任务处理
"""
import asyncio
from celery import shared_task
from sqlalchemy import select, update

from app.core.database import SessionLocal, async_session_maker
from app.models.notification import Notification
from app.models.post import Post
from app.services.risk_service import evaluate_content, RiskResult


@shared_task(name="tasks.run_risk_check_for_post")
def run_risk_check_for_post(post_id: str) -> None:
    """
    Celery 同步任务，内部运行异步风控检查
    """
    # 在同步上下文中运行异步函数
    result = asyncio.run(_async_risk_check(post_id))
    return result


async def _async_risk_check(post_id: str) -> None:
    """异步风控检查逻辑"""
    async with async_session_maker() as db:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            return

        risk_result: RiskResult = await evaluate_content(
            content=post.content,
            images=post.images if isinstance(post.images, list) else None,
        )

        status = (
            "approved"
            if risk_result.action == "approve"
            else ("rejected" if risk_result.action == "reject" else "pending")
        )
        await db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(
                risk_status=status,
                risk_score=risk_result.score,
                risk_reason=risk_result.reason,
            )
        )

        if risk_result.action == "reject" and risk_result.reason:
            notif = Notification(
                user_id=post.user_id,
                type="system",
                title="内容未通过审核",
                content=risk_result.reason,
                related_id=post_id,
            )
            db.add(notif)

        await db.commit()
