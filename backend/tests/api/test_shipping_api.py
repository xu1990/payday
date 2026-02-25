"""
测试物流和退货 API 端点 - Task 4.3 Phase 4
Shipping and Returns API Endpoints Tests

测试物流和退货相关的所有API端点：
- POST /orders/{order_id}/shipment - 创建发货记录（管理员）
- GET /orders/{order_id}/shipment - 获取发货信息
- PUT /shipments/{shipment_id}/tracking - 更新物流状态（管理员）
- POST /orders/{order_id}/returns - 创建退货申请
- GET /orders/{order_id}/returns - 获取退货列表
- PUT /returns/{return_id}/approve - 审批退货（管理员）
- PUT /returns/{return_id}/reject - 拒绝退货（管理员）
- POST /returns/{return_id}/refund - 处理退款（管理员）

测试覆盖：
- 成功场景
- 权限验证
- 数据验证
- 业务规则验证
- 错误处理
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.deps import get_current_admin, get_current_user
from app.core.exceptions import BusinessException, NotFoundException
from app.main import app
from app.models.admin import AdminUser
from app.models.shipping import OrderReturn, OrderShipment
from app.models.user import User
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# Mock get_current_user dependency
async def mock_get_current_user():
    """Mock current user for testing"""
    user = User(
        id="test-user-123",
        openid="test-openid-123",
        anonymous_name="测试用户",
        nickname="测试用户",
        avatar="https://example.com/avatar.jpg",
        status="normal"
    )
    return user


# Mock get_current_admin dependency
async def mock_get_current_admin():
    """Mock current admin for testing"""
    admin = AdminUser(
        id="admin-123",
        username="test_admin",
        role="admin",
        is_active="1"
    )
    return admin


class TestCreateShipmentEndpoint:
    """测试创建发货记录端点"""

    @pytest.mark.asyncio
    async def test_create_shipment_success(self):
        """测试管理员成功创建发货记录"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        shipment_mock = OrderShipment(
            id="shipment_123",
            order_id="order_123",
            courier_code="SF",
            courier_name="顺丰速运",
            tracking_number="SF1234567890",
            status="pending",
            shipped_at=datetime.utcnow(),
            tracking_info=None
        )

        try:
            with patch("app.services.shipping_service.ShippingService.create_shipment", new_callable=AsyncMock, return_value=shipment_mock):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    request_data = {
                        "courier_code": "SF",
                        "tracking_number": "SF1234567890"
                    }

                    response = await client.post(
                        "/api/v1/orders/order_123/shipment",
                        json=request_data,
                        headers={"Authorization": "Bearer admin_token"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["code"] == "SUCCESS"
                    assert data["message"] == "发货成功"
                    assert data["details"]["id"] == "shipment_123"
                    assert data["details"]["tracking_number"] == "SF1234567890"
        finally:
            app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_create_shipment_unauthorized(self):
        """测试未授权用户创建发货记录（需要admin权限）"""
        # This test verifies that non-admin users cannot create shipments
        # The endpoint requires get_current_admin dependency, so even with
        # a valid user token, it should fail authentication
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            request_data = {
                "courier_code": "SF",
                "tracking_number": "SF1234567890"
            }

            # No auth token - should get 401
            response = await client.post(
                "/api/v1/orders/order_123/shipment",
                json=request_data
            )

            # Should get 401 Unauthorized (no valid admin token)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_shipment_order_not_paid(self):
        """测试订单未支付时创建发货记录"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        with patch("app.services.shipping_service.ShippingService.create_shipment", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = BusinessException(
                "订单未支付，不能发货",
                code="ORDER_NOT_PAID"
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "courier_code": "SF",
                    "tracking_number": "SF1234567890"
                }

                response = await client.post(
                    "/api/v1/orders/order_123/shipment",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 400
                data = response.json()
                assert "订单未支付" in data["message"]

    @pytest.mark.asyncio
    async def test_create_shipment_already_shipped(self):
        """测试重复发货"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        with patch("app.services.shipping_service.ShippingService.create_shipment", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = BusinessException(
                "订单已发货",
                code="ALREADY_SHIPPED"
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "courier_code": "SF",
                    "tracking_number": "SF1234567890"
                }

                response = await client.post(
                    "/api/v1/orders/order_123/shipment",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 400
                data = response.json()
                assert "已发货" in data["message"]


class TestGetShipmentEndpoint:
    """测试获取发货信息端点"""

    @pytest.mark.asyncio
    async def test_get_shipment_success(self):
        """测试成功获取发货信息"""
        app.dependency_overrides[get_current_user] = mock_get_current_user

        shipment_mock = OrderShipment(
            id="shipment_123",
            order_id="order_123",
            courier_code="SF",
            courier_name="顺丰速运",
            tracking_number="SF1234567890",
            status="in_transit",
            shipped_at=datetime.utcnow(),
            delivered_at=None,
            tracking_info=[
                {"time": "2024-01-01 10:00", "status": "已揽收"},
                {"time": "2024-01-01 15:00", "status": "运输中"}
            ]
        )

        with patch("app.services.shipping_service.ShippingService.get_shipment_by_order_id", new_callable=AsyncMock, return_value=shipment_mock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/orders/order_123/shipment",
                    headers={"Authorization": "Bearer user_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["code"] == "SUCCESS"
                assert data["details"]["tracking_number"] == "SF1234567890"
                assert data["details"]["status"] == "in_transit"

    @pytest.mark.asyncio
    async def test_get_shipment_not_found(self):
        """测试获取不存在的发货信息"""
        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.services.shipping_service.ShippingService.get_shipment_by_order_id", new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/orders/order_999/shipment",
                    headers={"Authorization": "Bearer user_token"}
                )

                assert response.status_code == 404


class TestUpdateTrackingEndpoint:
    """测试更新物流状态端点"""

    @pytest.mark.asyncio
    async def test_update_tracking_success(self):
        """测试成功更新物流状态"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        shipment_mock = OrderShipment(
            id="shipment_123",
            order_id="order_123",
            courier_code="SF",
            courier_name="顺丰速运",
            tracking_number="SF1234567890",
            status="delivered",
            shipped_at=datetime.utcnow(),
            delivered_at=datetime.utcnow()
        )

        with patch("app.services.shipping_service.ShippingService.update_tracking_status", new_callable=AsyncMock, return_value=shipment_mock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "status": "delivered",
                    "tracking_info": [
                        {"time": "2024-01-02 10:00", "status": "已签收"}
                    ]
                }

                response = await client.put(
                    "/api/v1/shipments/shipment_123/tracking",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["code"] == "SUCCESS"
                assert data["message"] == "物流状态更新成功"
                assert data["details"]["status"] == "delivered"

    @pytest.mark.asyncio
    async def test_update_tracking_invalid_status(self):
        """测试更新无效的物流状态"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            request_data = {
                "status": "invalid_status"
            }

            response = await client.put(
                "/api/v1/shipments/shipment_123/tracking",
                json=request_data,
                headers={"Authorization": "Bearer admin_token"}
            )

            # Pydantic validation error
            assert response.status_code == 422


class TestCreateReturnRequestEndpoint:
    """测试创建退货申请端点"""

    @pytest.mark.asyncio
    async def test_create_return_success(self):
        """测试用户成功创建退货申请"""
        app.dependency_overrides[get_current_user] = mock_get_current_user

        return_mock = OrderReturn(
            id="return_123",
            order_id="order_123",
            order_item_id="item_123",
            return_reason="quality_issue",
            return_description="商品有质量问题",
            images=None,
            return_type="refund_only",
            status="requested",
            refund_amount=None,
            refund_transaction_id=None,
            requested_at=datetime.utcnow(),
            approved_at=None,
            completed_at=None,
            admin_id=None,
            admin_notes=None
        )

        with patch("app.services.shipping_service.ShippingService.create_return_request", new_callable=AsyncMock, return_value=return_mock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "order_item_id": "item_123",
                    "reason": "quality_issue",
                    "return_type": "refund_only",
                    "description": "商品有质量问题"
                }

                response = await client.post(
                    "/api/v1/orders/order_123/returns",
                    json=request_data,
                    headers={"Authorization": "Bearer user_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["code"] == "SUCCESS"
                assert data["message"] == "退货申请提交成功"
                assert data["details"]["id"] == "return_123"

    @pytest.mark.asyncio
    async def test_create_return_order_not_delivered(self):
        """测试订单未签收时创建退货"""
        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.services.shipping_service.ShippingService.create_return_request", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = BusinessException(
                "订单未签收，不能退货",
                code="ORDER_NOT_DELIVERED"
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "order_item_id": "item_123",
                    "reason": "quality_issue",
                    "return_type": "refund_only"
                }

                response = await client.post(
                    "/api/v1/orders/order_123/returns",
                    json=request_data,
                    headers={"Authorization": "Bearer user_token"}
                )

                assert response.status_code == 400
                data = response.json()
                assert "未签收" in data["message"]

    @pytest.mark.asyncio
    async def test_create_return_invalid_reason(self):
        """测试无效的退货原因"""
        app.dependency_overrides[get_current_user] = mock_get_current_user

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            request_data = {
                "order_item_id": "item_123",
                "reason": "invalid_reason",
                "return_type": "refund_only"
            }

            response = await client.post(
                "/api/v1/orders/order_123/returns",
                json=request_data,
                headers={"Authorization": "Bearer user_token"}
            )

            # Pydantic validation error
            assert response.status_code == 422


class TestGetReturnsEndpoint:
    """测试获取退货列表端点"""

    @pytest.mark.asyncio
    async def test_get_returns_success(self):
        """测试成功获取退货列表"""
        app.dependency_overrides[get_current_user] = mock_get_current_user

        return_mock1 = OrderReturn(
            id="return_123",
            order_id="order_123",
            order_item_id="item_123",
            return_reason="quality_issue",
            return_description="商品有质量问题",
            images=None,
            return_type="refund_only",
            status="requested",
            refund_amount=None,
            refund_transaction_id=None,
            requested_at=datetime.utcnow(),
            approved_at=None,
            completed_at=None,
            admin_id=None,
            admin_notes=None
        )

        return_mock2 = OrderReturn(
            id="return_124",
            order_id="order_123",
            order_item_id="item_124",
            return_reason="damaged",
            return_description="商品损坏",
            images=None,
            return_type="replace",
            status="approved",
            refund_amount=None,
            refund_transaction_id=None,
            requested_at=datetime.utcnow(),
            approved_at=datetime.utcnow(),
            completed_at=None,
            admin_id="admin_123",
            admin_notes="同意换货"
        )

        with patch("app.services.shipping_service.ShippingService.get_returns_by_order", new_callable=AsyncMock, return_value=[return_mock1, return_mock2]):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/orders/order_123/returns",
                    headers={"Authorization": "Bearer user_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["code"] == "SUCCESS"
                assert len(data["details"]) == 2

    @pytest.mark.asyncio
    async def test_get_returns_empty_list(self):
        """测试获取空的退货列表"""
        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.services.shipping_service.ShippingService.get_returns_by_order", new_callable=AsyncMock, return_value=[]):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/orders/order_123/returns",
                    headers={"Authorization": "Bearer user_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["code"] == "SUCCESS"
                assert len(data["details"]) == 0


class TestApproveReturnEndpoint:
    """测试审批退货端点"""

    @pytest.mark.asyncio
    async def test_approve_return_success(self):
        """测试管理员成功审批退货"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        return_mock = OrderReturn(
            id="return_123",
            order_id="order_123",
            order_item_id="item_123",
            return_reason="quality_issue",
            return_description="商品有质量问题",
            images=None,
            return_type="refund_only",
            status="approved",
            refund_amount=None,
            refund_transaction_id=None,
            requested_at=datetime.utcnow(),
            approved_at=datetime.utcnow(),
            completed_at=None,
            admin_id="admin_123",
            admin_notes="同意退货"
        )

        with patch("app.services.shipping_service.ShippingService.approve_return", new_callable=AsyncMock, return_value=return_mock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "notes": "同意退货"
                }

                response = await client.put(
                    "/api/v1/returns/return_123/approve",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["code"] == "SUCCESS"
                assert data["message"] == "退货审批通过"
                assert data["details"]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_approve_return_invalid_status(self):
        """测试审批状态不正确的退货"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        with patch("app.services.shipping_service.ShippingService.approve_return", new_callable=AsyncMock) as mock_approve:
            mock_approve.side_effect = BusinessException(
                "退货状态不正确，不能审批",
                code="INVALID_RETURN_STATUS"
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "notes": "同意退货"
                }

                response = await client.put(
                    "/api/v1/returns/return_123/approve",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 400
                data = response.json()
                assert "状态不正确" in data["message"]


class TestRejectReturnEndpoint:
    """测试拒绝退货端点"""

    @pytest.mark.asyncio
    async def test_reject_return_success(self):
        """测试管理员成功拒绝退货"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        return_mock = OrderReturn(
            id="return_123",
            order_id="order_123",
            order_item_id="item_123",
            return_reason="quality_issue",
            return_description="商品有质量问题",
            images=None,
            return_type="refund_only",
            status="rejected",
            refund_amount=None,
            refund_transaction_id=None,
            requested_at=datetime.utcnow(),
            approved_at=None,
            completed_at=None,
            admin_id="admin_123",
            admin_notes="不符合退货条件"
        )

        with patch("app.services.shipping_service.ShippingService.reject_return", new_callable=AsyncMock, return_value=return_mock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "notes": "不符合退货条件"
                }

                response = await client.put(
                    "/api/v1/returns/return_123/reject",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["code"] == "SUCCESS"
                assert data["message"] == "退货申请已拒绝"
                assert data["details"]["status"] == "rejected"


class TestProcessRefundEndpoint:
    """测试处理退款端点"""

    @pytest.mark.asyncio
    async def test_process_refund_success(self):
        """测试管理员成功处理退款"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        return_mock = OrderReturn(
            id="return_123",
            order_id="order_123",
            order_item_id="item_123",
            return_reason="quality_issue",
            return_description="商品有质量问题",
            images=None,
            return_type="refund_only",
            status="completed",
            refund_amount=Decimal("100.00"),
            refund_transaction_id="txn_123",
            requested_at=datetime.utcnow(),
            approved_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            admin_id="admin_123",
            admin_notes=None
        )

        with patch("app.services.shipping_service.ShippingService.process_refund", new_callable=AsyncMock, return_value=return_mock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "refund_amount": "100.00",
                    "transaction_id": "txn_123"
                }

                response = await client.post(
                    "/api/v1/returns/return_123/refund",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["code"] == "SUCCESS"
                assert data["message"] == "退款处理成功"
                assert data["details"]["status"] == "completed"
                assert data["details"]["refund_amount"] == "100.00"

    @pytest.mark.asyncio
    async def test_process_refund_invalid_amount(self):
        """测试处理退款时金额无效"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            request_data = {
                "refund_amount": "-50.00"
            }

            response = await client.post(
                "/api/v1/returns/return_123/refund",
                json=request_data,
                headers={"Authorization": "Bearer admin_token"}
            )

            # Pydantic validation error
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_process_refund_invalid_status(self):
        """测试退款状态不正确"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        with patch("app.services.shipping_service.ShippingService.process_refund", new_callable=AsyncMock) as mock_refund:
            mock_refund.side_effect = BusinessException(
                "退货状态不正确，不能退款",
                code="INVALID_RETURN_STATUS"
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "refund_amount": "100.00"
                }

                response = await client.post(
                    "/api/v1/returns/return_123/refund",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 400
                data = response.json()
                assert "状态不正确" in data["message"]


class TestShipmentEdgeCases:
    """测试发货边界情况"""

    @pytest.mark.asyncio
    async def test_create_shipment_invalid_courier(self):
        """测试使用无效物流公司创建发货"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        with patch("app.services.shipping_service.ShippingService.create_shipment", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = NotFoundException("物流公司不存在")

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "courier_code": "INVALID",
                    "tracking_number": "TRACK123"
                }

                response = await client.post(
                    "/api/v1/orders/order_123/shipment",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_tracking_shipment_not_found(self):
        """测试更新不存在的发货记录"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        with patch("app.services.shipping_service.ShippingService.update_tracking_status", new_callable=AsyncMock) as mock_update:
            mock_update.side_effect = NotFoundException("发货记录不存在")

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "status": "delivered"
                }

                response = await client.put(
                    "/api/v1/shipments/invalid_shipment/tracking",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 404


class TestReturnEdgeCases:
    """测试退货边界情况"""

    @pytest.mark.asyncio
    async def test_create_return_invalid_order_item(self):
        """测试使用无效订单项创建退货"""
        app.dependency_overrides[get_current_user] = mock_get_current_user

        with patch("app.services.shipping_service.ShippingService.create_return_request", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = NotFoundException("订单项不存在")

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "order_item_id": "invalid_item",
                    "reason": "quality_issue",
                    "return_type": "refund_only"
                }

                response = await client.post(
                    "/api/v1/orders/order_123/returns",
                    json=request_data,
                    headers={"Authorization": "Bearer user_token"}
                )

                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_approve_return_not_found(self):
        """测试审批不存在的退货"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        with patch("app.services.shipping_service.ShippingService.approve_return", new_callable=AsyncMock) as mock_approve:
            mock_approve.side_effect = NotFoundException("退货记录不存在")

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "notes": "同意退货"
                }

                response = await client.put(
                    "/api/v1/returns/invalid_return/approve",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reject_return_not_found(self):
        """测试拒绝不存在的退货"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        with patch("app.services.shipping_service.ShippingService.reject_return", new_callable=AsyncMock) as mock_reject:
            mock_reject.side_effect = NotFoundException("退货记录不存在")

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                request_data = {
                    "notes": "拒绝原因"
                }

                response = await client.put(
                    "/api/v1/returns/invalid_return/reject",
                    json=request_data,
                    headers={"Authorization": "Bearer admin_token"}
                )

                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_process_refund_zero_amount(self):
        """测试处理退款金额为0"""
        app.dependency_overrides[get_current_admin] = mock_get_current_admin

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            request_data = {
                "refund_amount": "0"
            }

            response = await client.post(
                "/api/v1/returns/return_123/refund",
                json=request_data,
                headers={"Authorization": "Bearer admin_token"}
            )

            # Pydantic validation error
            assert response.status_code == 422
