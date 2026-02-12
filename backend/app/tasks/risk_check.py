"""
发帖后异步风控检查：取帖子 → 文本/图片评分 → 更新 risk_status/risk_score/risk_reason；拒绝则下架并发系统通知
使用同步 Session（与 app.core.database SessionLocal 一致），由 FastAPI BackgroundTasks 在线程池执行
"""
from sqlalchemy import select, update

from app.core.database import SessionLocal
from app.models.notification import Notification
from app.models.post import Post
from app.services.risk_service import evaluate_content, RiskResult


def run_risk_check_for_post(post_id: str) -> None:
    db = SessionLocal()
    try:
        row = db.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()
        if not row:
            return
        post = row

        result: RiskResult = evaluate_content(
            content=post.content,
            images=post.images if isinstance(post.images, list) else None,
        )

        status = (
            "approved"
            if result.action == "approve"
            else ("rejected" if result.action == "reject" else "pending")
        )
        db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(
                risk_status=status,
                risk_score=result.score,
                risk_reason=result.reason,
            )
        )
        db.commit()

        if result.action == "reject" and result.reason:
            notif = Notification(
                user_id=post.user_id,
                type="system",
                title="内容未通过审核",
                content=result.reason,
                related_id=post_id,
            )
            db.add(notif)
            db.commit()
    finally:
        db.close()
