"""
支付 API 端点测试

测试 /api/v1/payment/* 路由的HTTP端点：
- POST /api/v1/payment/create - 创建支付订单
- POST /api/v1/payment/notify/wechat - 微信支付回调通知
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, Mock


@pytest.mark.asyncio
class TestCreatePaymentEndpoint:
    """测试POST /api/v1/payment/create端点"""

    def test_create_payment_success(
        self,
        client,
        user_headers,
        test_user,
        test_order,
        mock_wechat_pay,
    ):
        """测试创建支付成功 - 使用有效的订单ID"""
        # 使用TestClient发送HTTP POST请求（需要认证）
        response = client.post(
            "/api/v1/payment/create",
            json={"order_id": test_order.id},
            headers=user_headers,
        )

        # 验证HTTP响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["out_trade_no"] == test_order.id
        assert data["message"] == "支付参数生成成功"

    def test_create_payment_missing_order_id(
        self,
        client,
        user_headers,
    ):
        """测试创建支付失败 - 缺少order_id参数"""
        # 使用TestClient发送HTTP POST请求（缺少order_id）
        response = client.post(
            "/api/v1/payment/create",
            json={},
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回422验证错误
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_payment_order_not_found(
        self,
        client,
        user_headers,
        mock_wechat_pay,
    ):
        """测试创建支付失败 - 订单不存在"""
        # 使用TestClient发送HTTP POST请求（使用不存在的订单ID）
        response = client.post(
            "/api/v1/payment/create",
            json={"order_id": "non_existent_order_id"},
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回200但success为False
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "订单不存在" in data["message"]

    def test_create_payment_invalid_order_status(
        self,
        client,
        user_headers,
        test_user,
        test_membership,
        db_session,
        mock_wechat_pay,
    ):
        """测试创建支付失败 - 订单状态不正确（已支付）"""
        import asyncio

        # 创建一个已支付的订单
        from tests.test_utils import TestDataFactory

        order = asyncio.run(TestDataFactory.create_order(
            db_session,
            test_user.id,
            test_membership.id,
            status="paid",
        ))

        # 使用TestClient发送HTTP POST请求
        response = client.post(
            "/api/v1/payment/create",
            json={"order_id": order.id},
            headers=user_headers,
        )

        # 验证HTTP响应 - 应该返回200但success为False
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "订单状态不正确" in data["message"]

    def test_create_payment_user_no_openid(
        self,
        client,
        test_user,
        test_order,
        mock_wechat_pay,
    ):
        """测试创建支付失败 - 用户未绑定微信（没有openid）"""
        # 创建一个没有openid的用户token
        from app.core.security import create_access_token

        # 创建没有openid的用户
        user_no_openid = test_user
        user_no_openid.openid = None

        token = create_access_token(data={"sub": str(user_no_openid.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 使用TestClient发送HTTP POST请求
        response = client.post(
            "/api/v1/payment/create",
            json={"order_id": test_order.id},
            headers=headers,
        )

        # 验证HTTP响应 - 应该返回200但success为False
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "未绑定微信" in data["message"]

    def test_create_payment_unauthorized(
        self,
        client,
        test_order,
        mock_wechat_pay,
    ):
        """测试创建支付失败 - 未提供认证token"""
        # 使用TestClient发送HTTP POST请求（无认证）
        response = client.post(
            "/api/v1/payment/create",
            json={"order_id": test_order.id},
        )

        # 验证HTTP响应 - 应该返回401
        assert response.status_code == 401


@pytest.mark.asyncio
class TestWechatPaymentNotifyEndpoint:
    """测试POST /api/v1/payment/notify/wechat端点"""

    def test_payment_notify_success(
        self,
        client,
        test_order,
        mock_wechat_pay,
    ):
        """测试支付回调成功 - 处理有效的支付通知"""
        # 构造有效的支付通知XML
        notify_xml = self._build_notify_xml(
            out_trade_no=test_order.id,
            transaction_id="txn_test_123",
            total_fee=str(test_order.amount),
        )

        # 使用TestClient发送HTTP POST请求
        response = client.post(
            "/api/v1/payment/notify/wechat",
            content=notify_xml.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
        )

        # 验证HTTP响应 - 应该返回XML格式
        assert response.status_code == 200
        # 验证XML响应包含SUCCESS
        assert b"SUCCESS" in response.content

    def test_payment_notify_invalid_content_type(
        self,
        client,
        test_order,
    ):
        """测试支付回调失败 - Content-Type不正确"""
        # 使用TestClient发送HTTP POST请求（错误的Content-Type）
        response = client.post(
            "/api/v1/payment/notify/wechat",
            json={"data": "test"},
            headers={"Content-Type": "application/json"},
        )

        # 验证HTTP响应 - 应该返回XML格式
        assert response.status_code == 200
        # 验证XML响应包含FAIL
        assert b"FAIL" in response.content

    def test_payment_notify_invalid_xml(
        self,
        client,
        test_order,
    ):
        """测试支付回调失败 - 无效的XML格式"""
        # 使用TestClient发送HTTP POST请求（无效的XML）
        response = client.post(
            "/api/v1/payment/notify/wechat",
            content="invalid xml data",
            headers={"Content-Type": "application/xml"},
        )

        # 验证HTTP响应 - 应该返回XML格式
        assert response.status_code == 200
        # 验证XML响应包含FAIL
        assert b"FAIL" in response.content

    def test_payment_notify_order_not_found(
        self,
        client,
        mock_wechat_pay,
    ):
        """测试支付回调失败 - 订单不存在"""
        # 构造支付通知XML（使用不存在的订单ID）
        notify_xml = self._build_notify_xml(
            out_trade_no="non_existent_order_id",
            transaction_id="txn_test_123",
            total_fee="9900",
        )

        # 使用TestClient发送HTTP POST请求
        response = client.post(
            "/api/v1/payment/notify/wechat",
            content=notify_xml.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
        )

        # 验证HTTP响应 - 应该返回XML格式
        assert response.status_code == 200
        # 验证XML响应包含FAIL
        assert b"FAIL" in response.content

    def test_payment_notify_invalid_signature(
        self,
        client,
        test_order,
    ):
        """测试支付回调失败 - 签名验证失败"""
        # 构造签名无效的支付通知XML
        notify_xml = self._build_notify_xml(
            out_trade_no=test_order.id,
            transaction_id="txn_test_123",
            total_fee=str(test_order.amount),
            sign="invalid_sign",
        )

        # 使用TestClient发送HTTP POST请求
        response = client.post(
            "/api/v1/payment/notify/wechat",
            content=notify_xml.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
        )

        # 验证HTTP响应 - 应该返回XML格式
        assert response.status_code == 200
        # 验证XML响应包含FAIL
        assert b"FAIL" in response.content

    def _build_notify_xml(
        self,
        out_trade_no: str,
        transaction_id: str,
        total_fee: str,
        sign: str = None,
    ) -> str:
        """构造支付通知XML（用于测试）"""
        from app.core.config import get_settings
        from app.utils.wechat_pay import sign_md5, dict_to_xml

        settings = get_settings()

        # 构造通知数据
        notify_data = {
            "return_code": "SUCCESS",
            "result_code": "SUCCESS",
            "out_trade_no": out_trade_no,
            "transaction_id": transaction_id,
            "total_fee": total_fee,
            "time_end": "20241212143000",
        }

        # 生成签名（如果未提供）
        if sign is None:
            sign = sign_md5(notify_data, settings.wechat_pay_api_key)

        notify_data["sign"] = sign

        # 转换为XML
        return dict_to_xml(notify_data)
