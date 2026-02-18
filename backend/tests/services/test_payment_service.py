"""支付服务集成测试"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.payment_service import (
    create_membership_payment,
    handle_payment_notify,
    generate_payment_response,
)
from app.models.membership import MembershipOrder
from app.core.exceptions import NotFoundException, BusinessException
from tests.test_utils import TestDataFactory


def get_current_wechat_time():
    """生成当前时间的微信支付时间格式 (yyyyMMddHHmmss)"""
    return datetime.utcnow().strftime("%Y%m%d%H%M%S")


class TestCreateMembershipPayment:
    """测试创建会员订单支付"""

    @pytest.mark.asyncio
    async def test_create_payment_success(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试创建支付成功"""
        # 创建待支付订单
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=9900,
            status="pending",
        )

        # Mock微信支付接口
        with patch(
            "app.services.payment_service.create_mini_program_payment",
            new_callable=AsyncMock,
        ) as mock_create_payment:
            mock_create_payment.return_value = {
                "timeStamp": "1234567890",
                "nonceStr": "test_nonce",
                "package": "prepay_id=test_prepay_id",
                "signType": "MD5",
                "paySign": "test_sign",
                "out_trade_no": order.id,
            }

            # 调用创建支付
            result = await create_membership_payment(
                db_session,
                order_id=order.id,
                openid="test_openid_123",
                client_ip="127.0.0.1",
            )

            # 验证返回参数
            assert result is not None
            assert "timeStamp" in result
            assert "nonceStr" in result
            assert "package" in result
            assert "signType" in result
            assert "paySign" in result
            assert result["out_trade_no"] == order.id

            # 验证微信支付接口被正确调用
            mock_create_payment.assert_called_once()
            call_args = mock_create_payment.call_args
            assert call_args[1]["out_trade_no"] == order.id
            assert call_args[1]["total_fee"] == int(order.amount)
            assert call_args[1]["openid"] == "test_openid_123"

    @pytest.mark.asyncio
    async def test_create_payment_order_not_found(self, db_session: AsyncSession):
        """测试订单不存在"""
        with patch(
            "app.services.payment_service.create_mini_program_payment",
            new_callable=AsyncMock,
        ):
            with pytest.raises(NotFoundException) as exc_info:
                await create_membership_payment(
                    db_session,
                    order_id="nonexistent_order_id",
                    openid="test_openid",
                )

            assert "订单不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_payment_invalid_status(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试订单状态不正确"""
        # 创建已支付订单
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            status="paid",  # 已支付状态
        )

        with patch(
            "app.services.payment_service.create_mini_program_payment",
            new_callable=AsyncMock,
        ):
            with pytest.raises(BusinessException) as exc_info:
                await create_membership_payment(
                    db_session,
                    order_id=order.id,
                    openid="test_openid",
                )

            assert "订单状态不正确" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_payment_with_membership_name(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试支付描述包含会员套餐名称"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=9900,
            status="pending",
        )

        with patch(
            "app.services.payment_service.create_mini_program_payment",
            new_callable=AsyncMock,
        ) as mock_create_payment:
            mock_create_payment.return_value = {
                "timeStamp": "1234567890",
                "nonceStr": "test_nonce",
                "package": "prepay_id=test_prepay_id",
                "signType": "MD5",
                "paySign": "test_sign",
                "out_trade_no": order.id,
            }

            await create_membership_payment(
                db_session,
                order_id=order.id,
                openid="test_openid",
                client_ip="192.168.1.1",
            )

            # 验证支付描述包含会员名称
            call_args = mock_create_payment.call_args
            assert test_membership.name in call_args[1]["body"]


class TestHandlePaymentNotify:
    """测试处理支付回调通知"""

    @pytest.mark.asyncio
    async def test_handle_notify_success(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试处理支付通知成功"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=99.00,  # 99元
            status="pending",
        )

        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_123456",
            "total_fee": "9900",  # 99.00元 = 9900分
            "time_end": get_current_wechat_time(),  # 2024-12-15 14:30:00
        }

        result = await handle_payment_notify(db_session, notify_data)

        # 验证返回成功
        assert result is True

        # 刷新订单数据
        await db_session.refresh(order)

        # 验证订单状态更新
        assert order.status == "paid"
        assert order.payment_method == "wechat"
        assert order.transaction_id == "wx_txn_123456"
        assert order.start_date is not None
        assert order.end_date is not None

        # 验证会员期限计算正确
        expected_end_date = order.start_date + timedelta(days=test_membership.duration_days)
        assert order.end_date.date() == expected_end_date.date()

    @pytest.mark.asyncio
    async def test_handle_notify_idempotent(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试幂等性：重复通知应返回成功"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=99.00,
            status="pending",
        )

        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_123456",
            "total_fee": "9900",
            "time_end": get_current_wechat_time(),
        }

        # 第一次处理
        result1 = await handle_payment_notify(db_session, notify_data)
        assert result1 is True

        # 第二次处理（重复通知）
        result2 = await handle_payment_notify(db_session, notify_data)
        assert result2 is True

        # 验证订单状态保持不变
        await db_session.refresh(order)
        assert order.status == "paid"
        assert order.transaction_id == "wx_txn_123456"

    @pytest.mark.asyncio
    async def test_handle_notify_order_not_found(self, db_session: AsyncSession):
        """测试订单不存在"""
        notify_data = {
            "out_trade_no": "nonexistent_order_id",
            "transaction_id": "wx_txn_123",
            "total_fee": "9900",
            "time_end": get_current_wechat_time(),
        }

        result = await handle_payment_notify(db_session, notify_data)

        # 订单不存在应返回False，让微信重试
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_notify_missing_fields(self, db_session: AsyncSession):
        """测试缺少必需字段"""
        # 缺少 transaction_id
        notify_data = {
            "out_trade_no": "order_123",
            "total_fee": "9900",
            "time_end": get_current_wechat_time(),
        }

        result = await handle_payment_notify(db_session, notify_data)
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_notify_amount_mismatch(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试金额不匹配"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=99.00,  # 订单金额99元
            status="pending",
        )

        # 通知金额为100元（不匹配）
        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_123",
            "total_fee": "10000",  # 100元
            "time_end": get_current_wechat_time(),
        }

        result = await handle_payment_notify(db_session, notify_data)

        # 金额不匹配应返回False
        assert result is False

        # 验证订单状态未改变
        await db_session.refresh(order)
        assert order.status == "pending"

    @pytest.mark.asyncio
    async def test_handle_notify_different_transaction_id(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试不同的交易ID"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=99.00,
            status="paid",
            transaction_id="wx_txn_original",
        )

        # 尝试用不同的交易ID更新
        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_different",  # 不同的交易ID
            "total_fee": "9900",
            "time_end": get_current_wechat_time(),
        }

        result = await handle_payment_notify(db_session, notify_data)

        # 不同的交易ID应返回False
        assert result is False

        # 验证交易ID未改变
        await db_session.refresh(order)
        assert order.transaction_id == "wx_txn_original"

    @pytest.mark.asyncio
    async def test_handle_notify_invalid_time_format(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试无效的时间格式"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=99.00,
            status="pending",
        )

        # 无效的时间格式
        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_123",
            "total_fee": "9900",
            "time_end": "invalid_time_format",
        }

        result = await handle_payment_notify(db_session, notify_data)

        # SECURITY: 无效的时间格式应该被拒绝，防止恶意请求
        assert result is False

        # 验证订单状态未改变
        await db_session.refresh(order)
        assert order.status == "pending"

    @pytest.mark.asyncio
    async def test_handle_notify_decimal_precision(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试小数精度处理"""
        # 测试需要精确分的情况
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=99.99,  # 99.99元
            status="pending",
        )

        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_123",
            "total_fee": "9999",  # 9999分
            "time_end": get_current_wechat_time(),
        }

        result = await handle_payment_notify(db_session, notify_data)

        # 金额匹配应成功
        assert result is True
        await db_session.refresh(order)
        assert order.status == "paid"

    @pytest.mark.asyncio
    async def test_handle_notify_round_half_up(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试银行家舍入（四舍六入五取偶）"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=99.995,  # 需要舍入的情况
            status="pending",
        )

        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_123",
            "total_fee": "10000",  # 舍入后10000分
            "time_end": get_current_wechat_time(),
        }

        result = await handle_payment_notify(db_session, notify_data)

        # 验证舍入处理正确
        assert result is True
        await db_session.refresh(order)
        assert order.status == "paid"


class TestGeneratePaymentResponse:
    """测试生成支付回调响应"""

    def test_generate_success_response(self):
        """测试生成成功响应"""
        response = generate_payment_response("SUCCESS", "OK")

        assert response is not None
        assert "<return_code>SUCCESS</return_code>" in response
        assert "<return_msg>OK</return_msg>" in response
        assert "<xml>" in response
        assert "</xml>" in response

    def test_generate_fail_response(self):
        """测试生成失败响应"""
        response = generate_payment_response("FAIL", "签名失败")

        assert response is not None
        assert "<return_code>FAIL</return_code>" in response
        assert "<return_msg>签名失败</return_msg>" in response

    def test_generate_response_default_msg(self):
        """测试默认返回消息"""
        response = generate_payment_response("SUCCESS")

        assert response is not None
        assert "<return_msg>OK</return_msg>" in response


class TestPaymentServiceEdgeCases:
    """支付服务边界情况测试"""

    @pytest.mark.asyncio
    async def test_create_payment_with_zero_amount(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试零金额订单"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=0,
            status="pending",
        )

        with patch(
            "app.services.payment_service.create_mini_program_payment",
            new_callable=AsyncMock,
        ) as mock_create_payment:
            mock_create_payment.return_value = {
                "timeStamp": "1234567890",
                "nonceStr": "test_nonce",
                "package": "prepay_id=test_prepay_id",
                "signType": "MD5",
                "paySign": "test_sign",
                "out_trade_no": order.id,
            }

            result = await create_membership_payment(
                db_session,
                order_id=order.id,
                openid="test_openid",
            )

            assert result is not None
            mock_create_payment.assert_called_once_with(
                out_trade_no=order.id,
                total_fee=0,
                body=f"{test_membership.name}",
                openid="test_openid",
                client_ip="127.0.0.1",
            )

    @pytest.mark.asyncio
    async def test_handle_notify_with_invalid_amount(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试无效的金额格式"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=99.00,
            status="pending",
        )

        # 无效的金额格式
        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_123",
            "total_fee": "invalid_amount",
            "time_end": get_current_wechat_time(),
        }

        result = await handle_payment_notify(db_session, notify_data)

        # 无效金额应返回False
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_notify_paid_order_with_same_transaction(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试已支付订单收到相同交易ID的通知"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=99.00,
            status="paid",
            transaction_id="wx_txn_123",
        )

        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_123",  # 相同的交易ID
            "total_fee": "9900",
            "time_end": get_current_wechat_time(),
        }

        result = await handle_payment_notify(db_session, notify_data)

        # 应返回True（幂等性）
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_notify_concurrent_protection(
        self,
        db_session: AsyncSession,
        test_user,
        test_membership,
    ):
        """测试并发保护（使用行锁）"""
        order = await TestDataFactory.create_order(
            db_session,
            user_id=test_user.id,
            membership_id=test_membership.id,
            amount=99.00,
            status="pending",
        )

        notify_data = {
            "out_trade_no": order.id,
            "transaction_id": "wx_txn_123",
            "total_fee": "9900",
            "time_end": get_current_wechat_time(),
        }

        # 模拟两次并发处理
        # 在实际测试中很难模拟真正的并发，但可以验证逻辑路径
        result1 = await handle_payment_notify(db_session, notify_data)
        result2 = await handle_payment_notify(db_session, notify_data)

        # 两次都应返回成功（幂等性）
        assert result1 is True
        assert result2 is True

        # 验证订单只更新一次
        await db_session.refresh(order)
        assert order.status == "paid"
        assert order.transaction_id == "wx_txn_123"
