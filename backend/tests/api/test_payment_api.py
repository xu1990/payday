"""
支付 API 集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.mark.asyncio
async def test_create_payment_order(db_session: AsyncSession, user_headers: dict, test_membership):
    """测试创建支付订单"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payment_data = {
            "membership_id": test_membership.id,
            "payment_method": "wechat"
        }
        response = await client.post(
            "/api/v1/payment/create-order",
            headers=user_headers,
            json=payment_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "out_trade_no" in data
        assert "prepay_id" in data


@pytest.mark.asyncio
async def test_create_payment_without_auth():
    """测试未认证时创建支付订单"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/payment/create-order", json={})

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_payment_status(db_session: AsyncSession, user_headers: dict, test_order):
    """测试查询支付状态"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/payment/status?order_id={test_order.order_id}",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
        assert "status" in data


@pytest.mark.asyncio
async def test_handle_payment_callback(mock_wechat_pay):
    """测试处理微信支付回调"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        callback_data = {
            "out_trade_no": "test_order_123",
            "transaction_id": "wx_transaction_123",
            "total_fee": "9900"
        }
        response = await client.post(
            "/api/v1/payment/callback/wechat",
            json=callback_data
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_orders(db_session: AsyncSession, user_headers: dict, test_order):
    """测试获取订单列表"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/payment/orders", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
