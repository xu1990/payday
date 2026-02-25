"""
Shipping Service 测试 - 物流服务

测试覆盖：
1. create_shipment - 创建发货记录（成功、订单不存在、订单未支付、已发货）
2. get_shipment - 获取发货记录（成功、不存在）
3. update_tracking_status - 更新物流状态（成功、状态无效、发货记录不存在）
4. create_return_request - 创建退货申请（成功、订单不存在、订单项不存在、无权访问）
5. approve_return - 审批通过退货（成功、退货不存在、状态无效）
6. reject_return - 拒绝退货（成功、退货不存在、状态无效）
7. process_refund - 处理退款（成功、退货不存在、状态未到退款、金额无效）
8. get_returns_by_order - 获取订单退货列表（成功、空列表）
9. 业务逻辑验证（订单所有权、状态检查、金额验证）
10. 错误处理和异常场景
"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.order import Order, OrderItem
from app.models.shipping import CourierCompany, OrderReturn, OrderShipment
from app.models.user import User
from app.services.shipping_service import ShippingService
from sqlalchemy.ext.asyncio import AsyncSession


class TestCreateShipment:
    """测试创建发货记录"""

    @pytest.mark.asyncio
    async def test_create_shipment_success(self, db_session: AsyncSession):
        """测试创建发货成功"""
        # Create test user and order
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid")
        courier = await _create_test_courier(db_session)

        service = ShippingService()
        shipment = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        assert shipment is not None
        assert shipment.order_id == order.id
        assert shipment.courier_code == courier.code
        assert shipment.tracking_number == "SF1234567890"
        assert shipment.status == "pending"
        assert shipment.shipped_at is not None

    @pytest.mark.asyncio
    async def test_create_shipment_order_not_found(self, db_session: AsyncSession):
        """测试订单不存在"""
        service = ShippingService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.create_shipment(
                db=db_session,
                order_id="nonexistent_order",
                courier_code="SF",
                tracking_number="SF1234567890"
            )

        assert "订单不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_shipment_order_not_paid(self, db_session: AsyncSession):
        """测试订单未支付不能发货"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="pending")

        service = ShippingService()

        with pytest.raises(BusinessException) as exc_info:
            await service.create_shipment(
                db=db_session,
                order_id=order.id,
                courier_code="SF",
                tracking_number="SF1234567890"
            )

        assert "订单未支付" in str(exc_info.value)
        assert exc_info.value.code == "ORDER_NOT_PAID"

    @pytest.mark.asyncio
    async def test_create_shipment_already_shipped(self, db_session: AsyncSession):
        """测试订单已发货不能重复发货"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid")
        courier = await _create_test_courier(db_session)

        service = ShippingService()

        # First shipment
        await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        # Try to ship again
        with pytest.raises(BusinessException) as exc_info:
            await service.create_shipment(
                db=db_session,
                order_id=order.id,
                courier_code=courier.code,
                tracking_number="SF1234567891"
            )

        assert "订单已发货" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_shipment_updates_order_status(self, db_session: AsyncSession):
        """测试创建发货后更新订单状态为shipped"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid")
        courier = await _create_test_courier(db_session)

        service = ShippingService()
        await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        # Refresh order from database
        await db_session.refresh(order)
        assert order.status == "shipped"

    @pytest.mark.asyncio
    async def test_create_shipment_courier_not_found(self, db_session: AsyncSession):
        """测试物流公司不存在"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid")

        service = ShippingService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.create_shipment(
                db=db_session,
                order_id=order.id,
                courier_code="NONEXISTENT",
                tracking_number="SF1234567890"
            )

        assert "物流公司不存在" in str(exc_info.value)


class TestGetShipment:
    """测试获取发货记录"""

    @pytest.mark.asyncio
    async def test_get_shipment_success(self, db_session: AsyncSession):
        """测试获取发货记录成功"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid")
        courier = await _create_test_courier(db_session)

        service = ShippingService()
        created = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        shipment = await service.get_shipment(db=db_session, shipment_id=created.id)

        assert shipment is not None
        assert shipment.id == created.id
        assert shipment.tracking_number == "SF1234567890"

    @pytest.mark.asyncio
    async def test_get_shipment_not_found(self, db_session: AsyncSession):
        """测试发货记录不存在"""
        service = ShippingService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.get_shipment(db=db_session, shipment_id="nonexistent_shipment")

        assert "发货记录不存在" in str(exc_info.value)


class TestUpdateTrackingStatus:
    """测试更新物流状态"""

    @pytest.mark.asyncio
    async def test_update_tracking_status_success(self, db_session: AsyncSession):
        """测试更新物流状态成功"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid")
        courier = await _create_test_courier(db_session)

        service = ShippingService()
        shipment = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        tracking_info = [
            {"time": "2024-02-24 10:00", "status": "已揽收", "location": "深圳市"},
            {"time": "2024-02-24 15:00", "status": "运输中", "location": "广州市"}
        ]

        updated = await service.update_tracking_status(
            db=db_session,
            shipment_id=shipment.id,
            status="in_transit",
            tracking_info=tracking_info
        )

        assert updated.status == "in_transit"
        assert updated.tracking_info == tracking_info

    @pytest.mark.asyncio
    async def test_update_tracking_status_to_delivered(self, db_session: AsyncSession):
        """测试更新状态为已签收"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid")
        courier = await _create_test_courier(db_session)

        service = ShippingService()
        shipment = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        updated = await service.update_tracking_status(
            db=db_session,
            shipment_id=shipment.id,
            status="delivered",
            tracking_info=[{"time": "2024-02-24 18:00", "status": "已签收"}]
        )

        assert updated.status == "delivered"
        assert updated.delivered_at is not None
        assert updated.delivered_at.date() == datetime.now().date()

    @pytest.mark.asyncio
    async def test_update_tracking_status_updates_order(self, db_session: AsyncSession):
        """测试更新物流状态为已签收后更新订单状态"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="shipped")
        courier = await _create_test_courier(db_session)

        service = ShippingService()
        shipment = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        await service.update_tracking_status(
            db=db_session,
            shipment_id=shipment.id,
            status="delivered",
            tracking_info=[{"time": "2024-02-24 18:00", "status": "已签收"}]
        )

        await db_session.refresh(order)
        assert order.status == "delivered"

    @pytest.mark.asyncio
    async def test_update_tracking_status_shipment_not_found(self, db_session: AsyncSession):
        """测试发货记录不存在"""
        service = ShippingService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.update_tracking_status(
                db=db_session,
                shipment_id="nonexistent_shipment",
                status="in_transit",
                tracking_info=[]
            )

        assert "发货记录不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_tracking_status_invalid_status(self, db_session: AsyncSession):
        """测试无效的状态"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="paid")
        courier = await _create_test_courier(db_session)

        service = ShippingService()
        shipment = await service.create_shipment(
            db=db_session,
            order_id=order.id,
            courier_code=courier.code,
            tracking_number="SF1234567890"
        )

        with pytest.raises(ValidationException) as exc_info:
            await service.update_tracking_status(
                db=db_session,
                shipment_id=shipment.id,
                status="invalid_status",
                tracking_info=[]
            )

        assert "无效的物流状态" in str(exc_info.value)


class TestCreateReturnRequest:
    """测试创建退货申请"""

    @pytest.mark.asyncio
    async def test_create_return_request_success(self, db_session: AsyncSession):
        """测试创建退货申请成功"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()
        return_request = await service.create_return_request(
            db=db_session,
            order_id=order.id,
            order_item_id=order_item.id,
            reason="quality_issue",
            return_type="refund_only",
            description="商品有质量问题",
            images=["image1.jpg", "image2.jpg"]
        )

        assert return_request is not None
        assert return_request.order_id == order.id
        assert return_request.order_item_id == order_item.id
        assert return_request.return_reason == "quality_issue"
        assert return_request.return_type == "refund_only"
        assert return_request.status == "requested"
        assert return_request.return_description == "商品有质量问题"
        assert return_request.images == ["image1.jpg", "image2.jpg"]
        assert return_request.requested_at is not None

    @pytest.mark.asyncio
    async def test_create_return_request_order_not_found(self, db_session: AsyncSession):
        """测试订单不存在"""
        service = ShippingService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.create_return_request(
                db=db_session,
                order_id="nonexistent_order",
                order_item_id="item_123",
                reason="quality_issue",
                return_type="refund_only"
            )

        assert "订单不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_return_request_item_not_found(self, db_session: AsyncSession):
        """测试订单项不存在"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")

        service = ShippingService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.create_return_request(
                db=db_session,
                order_id=order.id,
                order_item_id="nonexistent_item",
                reason="quality_issue",
                return_type="refund_only"
            )

        assert "订单项不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_return_request_unauthorized(self, db_session: AsyncSession):
        """测试无权访问其他用户的订单"""
        user1 = await _create_test_user(db_session)
        user2 = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user1.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()

        # User2 tries to return User1's order
        with pytest.raises(BusinessException) as exc_info:
            await service.create_return_request(
                db=db_session,
                order_id=order.id,
                order_item_id=order_item.id,
                reason="quality_issue",
                return_type="refund_only",
                user_id=user2.id  # Different user
            )

        assert "无权访问此订单" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_return_request_order_not_delivered(self, db_session: AsyncSession):
        """测试未收货订单不能退货"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="shipped")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()

        with pytest.raises(BusinessException) as exc_info:
            await service.create_return_request(
                db=db_session,
                order_id=order.id,
                order_item_id=order_item.id,
                reason="quality_issue",
                return_type="refund_only"
            )

        assert "订单未签收，不能退货" in str(exc_info.value)
        assert exc_info.value.code == "ORDER_NOT_DELIVERED"

    @pytest.mark.asyncio
    async def test_create_return_request_invalid_reason(self, db_session: AsyncSession):
        """测试无效的退货原因"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()

        with pytest.raises(ValidationException) as exc_info:
            await service.create_return_request(
                db=db_session,
                order_id=order.id,
                order_item_id=order_item.id,
                reason="invalid_reason",
                return_type="refund_only"
            )

        assert "无效的退货原因" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_return_request_invalid_type(self, db_session: AsyncSession):
        """测试无效的退货类型"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()

        with pytest.raises(ValidationException) as exc_info:
            await service.create_return_request(
                db=db_session,
                order_id=order.id,
                order_item_id=order_item.id,
                reason="quality_issue",
                return_type="invalid_type"
            )

        assert "无效的退货类型" in str(exc_info.value)


class TestApproveReturn:
    """测试审批通过退货"""

    @pytest.mark.asyncio
    async def test_approve_return_success(self, db_session: AsyncSession):
        """测试审批通过退货成功"""
        user = await _create_test_user(db_session)
        admin = await _create_test_admin(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()
        return_request = await service.create_return_request(
            db=db_session,
            order_id=order.id,
            order_item_id=order_item.id,
            reason="quality_issue",
            return_type="refund_only"
        )

        approved = await service.approve_return(
            db=db_session,
            return_id=return_request.id,
            admin_id=admin.id,
            notes="同意退货"
        )

        assert approved.status == "approved"
        assert approved.admin_id == admin.id
        assert approved.admin_notes == "同意退货"
        assert approved.approved_at is not None

    @pytest.mark.asyncio
    async def test_approve_return_not_found(self, db_session: AsyncSession):
        """测试退货记录不存在"""
        admin = await _create_test_admin(db_session)
        service = ShippingService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.approve_return(
                db=db_session,
                return_id="nonexistent_return",
                admin_id=admin.id
            )

        assert "退货记录不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_approve_return_invalid_status(self, db_session: AsyncSession):
        """测试状态不正确不能审批"""
        user = await _create_test_user(db_session)
        admin = await _create_test_admin(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()
        return_request = await service.create_return_request(
            db=db_session,
            order_id=order.id,
            order_item_id=order_item.id,
            reason="quality_issue",
            return_type="refund_only"
        )

        # First approve
        await service.approve_return(
            db=db_session,
            return_id=return_request.id,
            admin_id=admin.id
        )

        # Try to approve again
        with pytest.raises(BusinessException) as exc_info:
            await service.approve_return(
                db=db_session,
                return_id=return_request.id,
                admin_id=admin.id
            )

        assert "退货状态不正确" in str(exc_info.value)


class TestRejectReturn:
    """测试拒绝退货"""

    @pytest.mark.asyncio
    async def test_reject_return_success(self, db_session: AsyncSession):
        """测试拒绝退货成功"""
        user = await _create_test_user(db_session)
        admin = await _create_test_admin(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()
        return_request = await service.create_return_request(
            db=db_session,
            order_id=order.id,
            order_item_id=order_item.id,
            reason="quality_issue",
            return_type="refund_only"
        )

        rejected = await service.reject_return(
            db=db_session,
            return_id=return_request.id,
            admin_id=admin.id,
            notes="不符合退货条件"
        )

        assert rejected.status == "rejected"
        assert rejected.admin_id == admin.id
        assert rejected.admin_notes == "不符合退货条件"

    @pytest.mark.asyncio
    async def test_reject_return_not_found(self, db_session: AsyncSession):
        """测试退货记录不存在"""
        admin = await _create_test_admin(db_session)
        service = ShippingService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.reject_return(
                db=db_session,
                return_id="nonexistent_return",
                admin_id=admin.id,
                notes="拒绝"
            )

        assert "退货记录不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reject_return_invalid_status(self, db_session: AsyncSession):
        """测试状态不正确不能拒绝"""
        user = await _create_test_user(db_session)
        admin = await _create_test_admin(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()
        return_request = await service.create_return_request(
            db=db_session,
            order_id=order.id,
            order_item_id=order_item.id,
            reason="quality_issue",
            return_type="refund_only"
        )

        # First reject
        await service.reject_return(
            db=db_session,
            return_id=return_request.id,
            admin_id=admin.id,
            notes="拒绝"
        )

        # Try to reject again
        with pytest.raises(BusinessException) as exc_info:
            await service.reject_return(
                db=db_session,
                return_id=return_request.id,
                admin_id=admin.id,
                notes="再次拒绝"
            )

        assert "退货状态不正确" in str(exc_info.value)


class TestProcessRefund:
    """测试处理退款"""

    @pytest.mark.asyncio
    async def test_process_refund_success(self, db_session: AsyncSession):
        """测试处理退款成功"""
        user = await _create_test_user(db_session)
        admin = await _create_test_admin(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered", final_amount=10000)
        order_item = await _create_test_order_item(db_session, order.id, subtotal=10000)

        service = ShippingService()
        return_request = await service.create_return_request(
            db=db_session,
            order_id=order.id,
            order_item_id=order_item.id,
            reason="quality_issue",
            return_type="refund_only"
        )

        await service.approve_return(
            db=db_session,
            return_id=return_request.id,
            admin_id=admin.id
        )

        refunded = await service.process_refund(
            db=db_session,
            return_id=return_request.id,
            refund_amount=Decimal("100.00"),
            transaction_id="refund_txn_123"
        )

        assert refunded.status == "completed"
        assert refunded.refund_amount == Decimal("100.00")
        assert refunded.refund_transaction_id == "refund_txn_123"
        assert refunded.completed_at is not None

    @pytest.mark.asyncio
    async def test_process_refund_not_found(self, db_session: AsyncSession):
        """测试退货记录不存在"""
        service = ShippingService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.process_refund(
                db=db_session,
                return_id="nonexistent_return",
                refund_amount=Decimal("100.00")
            )

        assert "退货记录不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_refund_invalid_status(self, db_session: AsyncSession):
        """测试状态不正确不能退款"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()
        return_request = await service.create_return_request(
            db=db_session,
            order_id=order.id,
            order_item_id=order_item.id,
            reason="quality_issue",
            return_type="refund_only"
        )

        # Try to refund before approval
        with pytest.raises(BusinessException) as exc_info:
            await service.process_refund(
                db=db_session,
                return_id=return_request.id,
                refund_amount=Decimal("100.00")
            )

        assert "退货状态不正确，不能退款" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_refund_negative_amount(self, db_session: AsyncSession):
        """测试退款金额不能为负数"""
        user = await _create_test_user(db_session)
        admin = await _create_test_admin(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()
        return_request = await service.create_return_request(
            db=db_session,
            order_id=order.id,
            order_item_id=order_item.id,
            reason="quality_issue",
            return_type="refund_only"
        )

        await service.approve_return(
            db=db_session,
            return_id=return_request.id,
            admin_id=admin.id
        )

        with pytest.raises(ValidationException) as exc_info:
            await service.process_refund(
                db=db_session,
                return_id=return_request.id,
                refund_amount=Decimal("-10.00")
            )

        assert "退款金额必须大于0" in str(exc_info.value)


class TestGetReturnsByOrder:
    """测试获取订单退货列表"""

    @pytest.mark.asyncio
    async def test_get_returns_by_order_success(self, db_session: AsyncSession):
        """测试获取订单退货列表成功"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")
        order_item = await _create_test_order_item(db_session, order.id)

        service = ShippingService()
        return1 = await service.create_return_request(
            db=db_session,
            order_id=order.id,
            order_item_id=order_item.id,
            reason="quality_issue",
            return_type="refund_only"
        )

        returns = await service.get_returns_by_order(db=db_session, order_id=order.id)

        assert len(returns) == 1
        assert returns[0].id == return1.id

    @pytest.mark.asyncio
    async def test_get_returns_by_order_empty(self, db_session: AsyncSession):
        """测试获取订单退货列表为空"""
        user = await _create_test_user(db_session)
        order = await _create_test_order(db_session, user.id, status="delivered")

        service = ShippingService()
        returns = await service.get_returns_by_order(db=db_session, order_id=order.id)

        assert len(returns) == 0

    @pytest.mark.asyncio
    async def test_get_returns_by_order_not_found(self, db_session: AsyncSession):
        """测试订单不存在"""
        service = ShippingService()

        with pytest.raises(NotFoundException) as exc_info:
            await service.get_returns_by_order(db=db_session, order_id="nonexistent_order")

        assert "订单不存在" in str(exc_info.value)


# Helper functions (module-level, accessible by all test classes)
async def _create_test_user(db: AsyncSession) -> User:
    """创建测试用户"""
    import uuid
    user = User(
        id=f"user_{uuid.uuid4().hex}",
        openid=f"openid_{uuid.uuid4().hex}",
        anonymous_name="测试用户",
        status="normal"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_test_admin(db: AsyncSession):
    """创建测试管理员"""
    import uuid

    from app.core.security import hash_password
    from app.models.admin import AdminUser

    admin = AdminUser(
        id=f"admin_{uuid.uuid4().hex}",
        username="test_admin",
        password_hash=hash_password("password"),
        role="admin"
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def _create_test_order(db: AsyncSession, user_id: str, status: str = "paid", final_amount: int = 10000) -> Order:
    """创建测试订单"""
    import uuid
    order = Order(
        id=f"order_{uuid.uuid4().hex}",
        user_id=user_id,
        order_number=f"ORD{datetime.now().strftime('%Y%m%d')}000001",
        total_amount=Decimal(str(final_amount)),
        points_used=0,
        discount_amount=Decimal("0"),
        shipping_cost=Decimal("0"),
        final_amount=Decimal(str(final_amount)),
        payment_method="wechat",
        payment_status="paid" if status in ["paid", "shipped", "delivered"] else "pending",
        status=status,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    if status == "paid":
        order.paid_at = datetime.utcnow()
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def _create_test_order_item(db: AsyncSession, order_id: str, subtotal: int = 10000) -> OrderItem:
    """创建测试订单项"""
    import uuid
    item = OrderItem(
        id=f"item_{uuid.uuid4().hex}",
        order_id=order_id,
        product_id=f"product_{uuid.uuid4().hex}",
        sku_id=f"sku_{uuid.uuid4().hex}",
        product_name="测试商品",
        sku_name="红色-L码",
        product_image="image.jpg",
        unit_price=Decimal(str(subtotal)),
        quantity=1,
        subtotal=Decimal(str(subtotal))
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def _create_test_courier(db: AsyncSession) -> CourierCompany:
    """创建测试物流公司"""
    import uuid
    courier = CourierCompany(
        id=f"courier_{uuid.uuid4().hex}",
        code="SF",
        name="顺丰速运",
        website="https://www.sf-express.com",
        tracking_url="https://www.sf-express.com/search",
        is_active=True
    )
    db.add(courier)
    await db.commit()
    await db.refresh(courier)
    return courier
