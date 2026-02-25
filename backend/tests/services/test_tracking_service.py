"""
Test suite for TrackingService.

Tests real-time logistics tracking integration with courier APIs.
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from app.core.exceptions import BusinessException, ValidationException
from app.models.tracking import Shipment, TrackingEvent, TrackingStatus
from app.schemas.tracking import TrackingEvent as TrackingEventSchema
from app.schemas.tracking import TrackingInfo
from app.services.tracking_service import TrackingService


class TestTrackingService:
    """Test suite for TrackingService."""

    @pytest.fixture
    def tracking_service(self):
        """Create tracking service instance."""
        return TrackingService()

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def sample_shipment(self):
        """Create sample shipment."""
        return Shipment(
            id=1,
            order_id=123,
            courier_code="SF",
            tracking_number="SF1234567890",
            status=TrackingStatus.SHIPPED,
            shipped_at=datetime.utcnow() - timedelta(days=1),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    @pytest.fixture
    def sample_tracking_info(self):
        """Create sample tracking info."""
        return TrackingInfo(
            tracking_number="SF1234567890",
            courier_code="SF",
            current_status="shipped",
            estimated_delivery=datetime.utcnow() + timedelta(days=2),
            events=[
                TrackingEventSchema(
                    status="shipped",
                    description="Package picked up",
                    location="Shenzhen, Guangdong",
                    timestamp=datetime.utcnow() - timedelta(days=1),
                ),
                TrackingEventSchema(
                    status="shipped",
                    description="Package in transit",
                    location="Guangzhou, Guangdong",
                    timestamp=datetime.utcnow() - timedelta(hours=12),
                ),
            ],
        )

    # ============ get_supported_couriers Tests ============

    def test_get_supported_couriers(self, tracking_service):
        """Test getting list of supported couriers."""
        couriers = tracking_service.get_supported_couriers()

        assert isinstance(couriers, list)
        assert len(couriers) > 0

        # Verify structure
        courier = couriers[0]
        assert "code" in courier
        assert "name" in courier
        assert "enabled" in courier

        # Verify common couriers are present
        courier_codes = [c["code"] for c in couriers]
        assert "SF" in courier_codes  # 顺丰
        assert "YTO" in courier_codes  # 圆通
        assert "STO" in courier_codes  # 申通
        assert "ZTO" in courier_codes  # 中通
        assert "Yunda" in courier_codes  # 韵达

    def test_get_supported_couriers_filters_enabled(self, tracking_service):
        """Test that only enabled couriers are returned."""
        couriers = tracking_service.get_supported_couriers()

        # All returned couriers should be enabled
        assert all(c["enabled"] for c in couriers)

    # ============ parse_tracking_response Tests ============

    @pytest.mark.asyncio
    async def test_parse_tracking_response_sf(
        self, tracking_service, sample_tracking_info
    ):
        """Test parsing SF (Shunfeng) tracking response."""
        response_data = {
            "state": "2",  # In transit
            "data": [
                {
                    "time": "2024-02-20 10:00:00",
                    "context": "Package picked up",
                    "location": "Shenzhen, Guangdong",
                },
                {
                    "time": "2024-02-20 22:00:00",
                    "context": "Package in transit",
                    "location": "Guangzhou, Guangdong",
                },
            ],
        }

        parsed = await tracking_service.parse_tracking_response("SF", response_data)

        assert parsed.current_status == "shipped"
        assert len(parsed.events) == 2
        assert parsed.events[0].description == "Package picked up"
        assert parsed.events[0].location == "Shenzhen, Guangdong"

    @pytest.mark.asyncio
    async def test_parse_tracking_response_yto(self, tracking_service):
        """Test parsing YTO (Yuantong) tracking response."""
        response_data = {
            "state": "2",  # In transit
            "data": [
                {
                    "time": "2024-02-20 10:00:00",
                    "context": "Package picked up",
                    "location": "Shenzhen",
                },
                {
                    "time": "2024-02-20 22:00:00",
                    "context": "Package in transit",
                    "location": "Guangzhou",
                },
            ],
        }

        parsed = await tracking_service.parse_tracking_response("YTO", response_data)

        assert parsed.current_status == "shipped"
        assert len(parsed.events) == 2
        assert parsed.events[0].description == "Package picked up"

    @pytest.mark.asyncio
    async def test_parse_tracking_response_delivered(self, tracking_service):
        """Test parsing delivered status."""
        response_data = {
            "state": "3",  # Delivered
            "data": [
                {
                    "time": "2024-02-20 10:00:00",
                    "context": "Package delivered",
                    "location": "Beijing",
                }
            ],
        }

        parsed = await tracking_service.parse_tracking_response("SF", response_data)

        assert parsed.current_status == "delivered"
        assert len(parsed.events) == 1

    @pytest.mark.asyncio
    async def test_parse_tracking_response_empty(self, tracking_service):
        """Test parsing response with no tracking data."""
        response_data = {"state": "0", "data": []}

        parsed = await tracking_service.parse_tracking_response("SF", response_data)

        assert parsed.current_status == "pending"
        assert len(parsed.events) == 0

    @pytest.mark.asyncio
    async def test_parse_tracking_response_unsupported_courier(
        self, tracking_service
    ):
        """Test parsing response for unsupported courier."""
        response_data = {"data": []}

        with pytest.raises(BusinessException) as exc_info:
            await tracking_service.parse_tracking_response("UNSUPPORTED", response_data)

        assert "不支持的快递公司" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_tracking_response_invalid_format(self, tracking_service):
        """Test parsing malformed response."""
        response_data = {"invalid": "data"}

        with pytest.raises(BusinessException) as exc_info:
            await tracking_service.parse_tracking_response("SF", response_data)

        assert "解析失败" in str(exc_info.value)

    # ============ fetch_tracking_info Tests ============

    @pytest.mark.asyncio
    async def test_fetch_tracking_info_success(
        self, tracking_service, sample_tracking_info
    ):
        """Test successfully fetching tracking info from API."""
        with patch.object(
            tracking_service, "_call_courier_api", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = {
                "state": "2",
                "data": [
                    {
                        "time": "2024-02-20 10:00:00",
                        "context": "Package picked up",
                        "location": "Shenzhen",
                    }
                ],
            }

            result = await tracking_service.fetch_tracking_info("SF", "SF1234567890")

            assert result.current_status == "shipped"
            assert len(result.events) == 1
            mock_api.assert_called_once_with("SF", "SF1234567890")

    @pytest.mark.asyncio
    async def test_fetch_tracking_info_api_error(self, tracking_service):
        """Test handling API errors during fetch."""
        with patch.object(
            tracking_service, "_call_courier_api", new_callable=AsyncMock
        ) as mock_api:
            mock_api.side_effect = httpx.HTTPStatusError(
                "API Error", request=Mock(), response=Mock(status_code=500)
            )

            with pytest.raises(BusinessException) as exc_info:
                await tracking_service.fetch_tracking_info("SF", "SF1234567890")

            assert "物流API调用失败" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_tracking_info_timeout(self, tracking_service):
        """Test handling API timeout."""
        with patch.object(
            tracking_service, "_call_courier_api", new_callable=AsyncMock
        ) as mock_api:
            mock_api.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(BusinessException) as exc_info:
                await tracking_service.fetch_tracking_info("SF", "SF1234567890")

            assert "物流API调用超时" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_tracking_info_invalid_params(self, tracking_service):
        """Test validation of input parameters."""
        with pytest.raises(ValidationException) as exc_info:
            await tracking_service.fetch_tracking_info("", "SF1234567890")

        assert "快递公司代码不能为空" in str(exc_info.value)

        with pytest.raises(ValidationException) as exc_info:
            await tracking_service.fetch_tracking_info("SF", "")

        assert "物流单号不能为空" in str(exc_info.value)

    # ============ update_shipment_tracking Tests ============

    @pytest.mark.asyncio
    async def test_update_shipment_tracking_success(
        self,
        tracking_service,
        mock_db_session,
        sample_shipment,
        sample_tracking_info,
    ):
        """Test successfully updating shipment tracking."""
        # Mock the execute chain - execute returns a coroutine that resolves to a result object
        async def mock_execute(*args, **kwargs):
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_shipment
            return mock_result

        mock_db_session.execute = mock_execute
        mock_db_session.commit = AsyncMock()

        # Mock refresh to keep the shipment object as-is (with the updated status)
        async def mock_refresh(shipment_obj):
            # The shipment object has already been updated in place
            pass

        mock_db_session.refresh = mock_refresh

        result = await tracking_service.update_shipment_tracking(
            mock_db_session, 1, sample_tracking_info
        )

        assert result is not None
        assert result.status == "shipped"
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_update_shipment_tracking_not_found(
        self, tracking_service, mock_db_session, sample_tracking_info
    ):
        """Test updating non-existent shipment."""
        # Mock the execute chain to return None
        async def mock_execute(*args, **kwargs):
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            return mock_result

        mock_db_session.execute = mock_execute

        with pytest.raises(BusinessException) as exc_info:
            await tracking_service.update_shipment_tracking(
                mock_db_session, 999, sample_tracking_info
            )

        assert "物流记录不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_shipment_tracking_delivered(
        self,
        tracking_service,
        mock_db_session,
        sample_shipment,
        sample_tracking_info,
    ):
        """Test updating shipment to delivered status."""
        sample_tracking_info.current_status = "delivered"
        sample_tracking_info.events = [
            TrackingEventSchema(
                status="delivered",
                description="Package delivered",
                location="Beijing",
                timestamp=datetime.utcnow(),
            )
        ]

        # Mock the execute chain
        async def mock_execute(*args, **kwargs):
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_shipment
            return mock_result

        mock_db_session.execute = mock_execute
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        result = await tracking_service.update_shipment_tracking(
            mock_db_session, 1, sample_tracking_info
        )

        assert result.status == TrackingStatus.DELIVERED
        assert result.delivered_at is not None

    @pytest.mark.asyncio
    async def test_update_shipment_tracking_events_saved(
        self,
        tracking_service,
        mock_db_session,
        sample_shipment,
        sample_tracking_info,
    ):
        """Test that tracking events are saved to database."""
        # Track execute calls
        execute_call_count = [0]

        async def mock_execute(*args, **kwargs):
            mock_result = Mock()
            if execute_call_count[0] == 0:
                # First call - fetch shipment
                mock_result.scalar_one_or_none.return_value = sample_shipment
            else:
                # Subsequent calls - check existing events
                mock_result.scalar_one_or_none.return_value = None
            execute_call_count[0] += 1
            return mock_result

        mock_db_session.execute = mock_execute
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        await tracking_service.update_shipment_tracking(
            mock_db_session, 1, sample_tracking_info
        )

        # Should add tracking events
        assert mock_db_session.add.called

    # ============ batch_update_tracking Tests ============

    @pytest.mark.asyncio
    async def test_batch_update_tracking_success(
        self, tracking_service, mock_db_session, sample_shipment
    ):
        """Test batch updating all pending shipments."""
        # Mock execute to return pending shipments
        async def mock_execute(*args, **kwargs):
            mock_result = Mock()
            mock_scalars = Mock()
            mock_scalars.all.return_value = [sample_shipment]
            mock_result.scalars.return_value = mock_scalars
            return mock_result

        mock_db_session.execute = mock_execute

        # Mock fetch_tracking_info
        with patch.object(
            tracking_service, "fetch_tracking_info", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = TrackingInfo(
                tracking_number="SF1234567890",
                courier_code="SF",
                current_status="shipped",
                events=[],
            )

            result = await tracking_service.batch_update_tracking(mock_db_session)

            assert result["total"] == 1
            assert result["updated"] == 1
            assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_batch_update_tracking_partial_failure(
        self, tracking_service, mock_db_session
    ):
        """Test batch update with some failures."""
        shipment1 = Shipment(
            id=1,
            order_id=123,
            courier_code="SF",
            tracking_number="SF1234567890",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        shipment2 = Shipment(
            id=2,
            order_id=124,
            courier_code="YTO",
            tracking_number="YTO9876543210",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Mock execute to return shipments
        async def mock_execute(*args, **kwargs):
            mock_result = Mock()
            mock_scalars = Mock()
            mock_scalars.all.return_value = [shipment1, shipment2]
            mock_result.scalars.return_value = mock_scalars
            return mock_result

        mock_db_session.execute = mock_execute

        with patch.object(
            tracking_service, "fetch_tracking_info", new_callable=AsyncMock
        ) as mock_fetch:
            # First succeeds, second fails
            mock_fetch.side_effect = [
                TrackingInfo(
                    tracking_number="SF1234567890",
                    courier_code="SF",
                    current_status="shipped",
                    events=[],
                ),
                BusinessException("API Error"),
            ]

            result = await tracking_service.batch_update_tracking(mock_db_session)

            assert result["total"] == 2
            assert result["updated"] == 1
            assert result["failed"] == 1

    @pytest.mark.asyncio
    async def test_batch_update_tracking_no_pending(
        self, tracking_service, mock_db_session
    ):
        """Test batch update when no pending shipments."""
        # Mock execute to return empty list
        async def mock_execute(*args, **kwargs):
            mock_result = Mock()
            mock_scalars = Mock()
            mock_scalars.all.return_value = []
            mock_result.scalars.return_value = mock_scalars
            return mock_result

        mock_db_session.execute = mock_execute

        result = await tracking_service.batch_update_tracking(mock_db_session)

        assert result["total"] == 0
        assert result["updated"] == 0
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_batch_update_tracking_continues_on_error(
        self, tracking_service, mock_db_session
    ):
        """Test that batch update continues even when one update fails."""
        shipments = [
            Shipment(
                id=i,
                order_id=100 + i,
                courier_code="SF",
                tracking_number=f"SF{i}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i in range(1, 6)
        ]

        # Mock execute to return shipments
        async def mock_execute(*args, **kwargs):
            mock_result = Mock()
            mock_scalars = Mock()
            mock_scalars.all.return_value = shipments
            mock_result.scalars.return_value = mock_scalars
            return mock_result

        mock_db_session.execute = mock_execute

        with patch.object(
            tracking_service, "fetch_tracking_info", new_callable=AsyncMock
        ) as mock_fetch:
            # Third shipment fails
            mock_fetch.side_effect = [
                TrackingInfo(
                    tracking_number=f"SF{i}",
                    courier_code="SF",
                    current_status="shipped",
                    events=[],
                )
                if i != 3
                else BusinessException("API Error")
                for i in range(1, 6)
            ]

            result = await tracking_service.batch_update_tracking(mock_db_session)

            # Should process all shipments despite one failure
            assert result["total"] == 5
            assert result["updated"] == 4
            assert result["failed"] == 1
