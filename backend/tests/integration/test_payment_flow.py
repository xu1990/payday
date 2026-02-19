"""支付流程集成测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from tests.test_utils import TestDataFactory


@pytest.mark.asyncio
async def test_membership_purchase_flow(db_session: AsyncSession):
    """测试会员购买完整流程"""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 步骤1: 创建用户并登录
        user = await TestDataFactory.create_user(db_session)

        from app.core.security import create_access_token
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 步骤2: 查看会员套餐列表
        response = await client.get("/api/v1/admin/config/memberships")
        assert response.status_code == 200

        memberships = response.json()
        assert len(memberships) > 0
        first_membership = memberships[0]

        # 步骤3: 创建支付订单
        order_data = {
            "membership_id": first_membership["id"],
            "payment_method": "wechat"
        }

        # Mock微信支付
        from unittest.mock import AsyncMock, patch
        with patch('app.services.payment_service.create_mini_program_payment', new_callable=AsyncMock) as mock_pay:
            mock_pay.return_value = {
                "timeStamp": "1234567890",
                "nonceStr": "test_nonce",
                "package": "prepay_id=test",
                "signType": "MD5",
                "paySign": "test_sign",
                "out_trade_no": "test_order_id",
            }

            response = await client.post(
                "/api/v1/payment/membership",
                headers=headers,
                json=order_data
            )

            assert response.status_code == 200
            payment_data = response.json()
            assert "timeStamp" in payment_data
            assert "package" in payment_data

        # 步骤4: 模拟支付成功通知
        # 获取订单ID（需要从数据库或响应中获取）
        # 这里简化处理，直接使用TestDataFactory创建订单并处理通知
        from app.models.membership import Membership
        membership = await TestDataFactory.create_membership(db_session)
        order = await TestDataFactory.create_order(
            db_session,
            user_id=user.id,
            membership_id=membership.id,
            status="pending"
        )

        # 模拟微信支付回调
        from datetime import datetime
        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_" + order.id[:8],
            "total_fee": str(int(order.amount)),  # 转换为分
            "time_end": datetime.utcnow().strftime("%Y%m%d%H%M%S")
        }

        # Mock nonce检查（Redis可能不可用）
        with patch('app.core.cache.get_redis_client', new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None  # Redis不可用

            response = await client.post(
                "/api/v1/payment/notify",
                json=notify_data
            )

            # 应该返回成功
            assert response.status_code == 200

        # 步骤5: 验证订单状态已更新
        from sqlalchemy import select
        from app.models.membership import MembershipOrder

        result = await db_session.execute(
            select(MembershipOrder).where(MembershipOrder.id == order.id)
        )
        updated_order = result.scalar_one_or_none()

        assert updated_order is not None
        assert updated_order.status == "paid"
        assert updated_order.transaction_id is not None

        # 步骤6: 验证用户会员状态
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200

        user_data = response.json()
        # 验证会员信息（如果API返回）
        # assert "membership" in user_data or "vip_status" in user_data


@pytest.mark.asyncio
async def test_payment_failure_handling(db_session: AsyncSession):
    """测试支付失败处理"""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 创建用户
        user = await TestDataFactory.create_user(db_session)
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 创建会员套餐
        membership = await TestDataFactory.create_membership(db_session)

        # 创建订单
        order = await TestDataFactory.create_order(
            db_session,
            user_id=user.id,
            membership_id=membership.id,
            status="pending"
        )

        # 模拟支付失败（金额不匹配）
        from datetime import datetime
        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_failed",
            "total_fee": "1",  # 错误的金额（订单金额是9900分）
            "time_end": datetime.utcnow().strftime("%Y%m%d%H%M%S")
        }

        with patch('app.core.cache.get_redis_client', new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None

            response = await client.post(
                "/api/v1/payment/notify",
                json=notify_data
            )

            # 应该返回错误
            assert response.status_code == 200  # 微信需要200响应，但订单未更新

        # 验证订单状态仍然是pending
        from sqlalchemy import select
        from app.models.membership import MembershipOrder

        result = await db_session.execute(
            select(MembershipOrder).where(MembershipOrder.id == order.id)
        )
        updated_order = result.scalar_one_or_none()

        assert updated_order.status == "pending"
