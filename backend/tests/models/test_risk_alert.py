"""
单元测试 - 风险预警模型 (app.models.risk_alert)
"""
import pytest
from datetime import datetime
from sqlalchemy import select

from app.models.risk_alert import RiskAlert


class TestRiskAlert:
    """测试风险预警模型"""

    def test_table_name(self):
        """测试表名"""
        assert RiskAlert.__tablename__ == "risk_alerts"

    def test_columns(self):
        """测试列定义"""
        # 验证列存在
        assert hasattr(RiskAlert, 'id')
        assert hasattr(RiskAlert, 'user_id')
        assert hasattr(RiskAlert, 'target_type')
        assert hasattr(RiskAlert, 'target_id')
        assert hasattr(RiskAlert, 'risk_score')
        assert hasattr(RiskAlert, 'risk_reason')
        assert hasattr(RiskAlert, 'is_handled')
        assert hasattr(RiskAlert, 'handled_by')
        assert hasattr(RiskAlert, 'handled_at')
        assert hasattr(RiskAlert, 'created_at')

    @pytest.mark.asyncio
    async def test_create_instance(self, db_session):
        """测试创建实例"""
        alert = RiskAlert(
            user_id="test_user_id",
            target_type="post",
            target_id="test_post_id",
            risk_score=85,
            risk_reason="包含敏感词汇",
        )

        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)

        assert alert.id is not None
        assert alert.user_id == "test_user_id"
        assert alert.target_type == "post"
        assert alert.target_id == "test_post_id"
        assert alert.risk_score == 85
        assert alert.risk_reason == "包含敏感词汇"
        assert alert.is_handled is False
        assert alert.created_at is not None

    @pytest.mark.asyncio
    async def test_default_values(self, db_session):
        """测试默认值"""
        alert = RiskAlert(
            user_id="test_user_id",
            target_type="comment",
            target_id="test_comment_id",
            risk_score=50,
        )

        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)

        assert alert.is_handled is False
        assert alert.created_at is not None
        assert alert.risk_reason is None
        assert alert.handled_by is None
        assert alert.handled_at is None

    @pytest.mark.asyncio
    async def test_handled_status(self, db_session):
        """测试处理状态"""
        alert = RiskAlert(
            user_id="test_user_id",
            target_type="post",
            target_id="test_post_id",
            risk_score=90,
        )

        db_session.add(alert)
        await db_session.commit()

        # 标记为已处理
        alert.is_handled = True
        alert.handled_by = "admin_user_id"
        alert.handled_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(alert)

        assert alert.is_handled is True
        assert alert.handled_by == "admin_user_id"
        assert alert.handled_at is not None

    @pytest.mark.asyncio
    async def test_target_types(self, db_session):
        """测试不同目标类型"""
        target_types = ["post", "comment"]

        for idx, target_type in enumerate(target_types):
            alert = RiskAlert(
                user_id="test_user_id",
                target_type=target_type,
                target_id=f"target_{idx}",
                risk_score=70 + idx * 10,
            )
            db_session.add(alert)

        await db_session.commit()

        # 验证所有类型都创建成功
        alerts = await db_session.execute(
            select(RiskAlert).where(RiskAlert.user_id == "test_user_id")
        )
        results = list(alerts.scalars().all())
        assert len(results) == len(target_types)
        assert {a.target_type for a in results} == set(target_types)

    @pytest.mark.asyncio
    async def test_risk_score_range(self, db_session):
        """测试风险评分范围"""
        scores = [0, 50, 100]

        for score in scores:
            alert = RiskAlert(
                user_id="test_user_id",
                target_type="post",
                target_id=f"target_{score}",
                risk_score=score,
            )
            db_session.add(alert)

        await db_session.commit()

        # 验证所有评分都创建成功
        alerts = await db_session.execute(
            select(RiskAlert).where(RiskAlert.user_id == "test_user_id")
        )
        results = list(alerts.scalars().all())
        assert len(results) == len(scores)
        assert {a.risk_score for a in results} == set(scores)

    @pytest.mark.asyncio
    async def test_optional_risk_reason(self, db_session):
        """测试可选风险原因"""
        alert = RiskAlert(
            user_id="test_user_id",
            target_type="comment",
            target_id="test_comment_id",
            risk_score=60,
            # risk_reason 不设置
        )

        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)

        assert alert.risk_score == 60
        assert alert.risk_reason is None

    @pytest.mark.asyncio
    async def test_handled_by_optional(self, db_session):
        """测试 handled_by 可选"""
        # 创建已处理但没有处理人的情况（可能自动处理）
        alert = RiskAlert(
            user_id="test_user_id",
            target_type="post",
            target_id="test_post_id",
            risk_score=75,
            is_handled=True,
        )

        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)

        assert alert.is_handled is True
        assert alert.handled_by is None
        assert alert.handled_at is None

    @pytest.mark.asyncio
    async def test_filter_by_handled_status(self, db_session):
        """测试按处理状态筛选"""
        # 创建未处理的预警
        for i in range(3):
            alert = RiskAlert(
                user_id="test_user_id",
                target_type="post",
                target_id=f"unhandled_{i}",
                risk_score=70,
                is_handled=False,
            )
            db_session.add(alert)

        # 创建已处理的预警
        for i in range(2):
            alert = RiskAlert(
                user_id="test_user_id",
                target_type="post",
                target_id=f"handled_{i}",
                risk_score=70,
                is_handled=True,
                handled_by="admin_id",
                handled_at=datetime.utcnow(),
            )
            db_session.add(alert)

        await db_session.commit()

        # 查询未处理的
        unhandled = await db_session.execute(
            select(RiskAlert).where(
                RiskAlert.user_id == "test_user_id",
                RiskAlert.is_handled == False,
            )
        )
        assert len(list(unhandled.scalars().all())) == 3

        # 查询已处理的
        handled = await db_session.execute(
            select(RiskAlert).where(
                RiskAlert.user_id == "test_user_id",
                RiskAlert.is_handled == True,
            )
        )
        assert len(list(handled.scalars().all())) == 2
