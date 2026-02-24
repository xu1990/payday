"""
Real-time logistics tracking service.

Integrates with courier APIs (Kuaidi100, KDNiao, etc.) to fetch
and update shipment tracking information.
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.tracking import Shipment, TrackingEvent, TrackingStatus
from app.schemas.tracking import TrackingInfo, TrackingEvent as TrackingEventSchema
from app.core.exceptions import BusinessException, ValidationException


logger = logging.getLogger(__name__)


class TrackingService:
    """
    Service for real-time logistics tracking.

    Supports multiple Chinese courier companies through standardized APIs.
    """

    # Supported courier configurations
    SUPPORTED_COURIERS = {
        "SF": {
            "name": "顺丰速运",
            "api_type": "kuaidi100",
            "code_kuaidi100": "sf",
            "code_kdniao": "SF",
            "enabled": True,
        },
        "YTO": {
            "name": "圆通速递",
            "api_type": "kuaidi100",
            "code_kuaidi100": "yuantong",
            "code_kdniao": "YTO",
            "enabled": True,
        },
        "STO": {
            "name": "申通快递",
            "api_type": "kuaidi100",
            "code_kuaidi100": "shentong",
            "code_kdniao": "STO",
            "enabled": True,
        },
        "ZTO": {
            "name": "中通快递",
            "api_type": "kuaidi100",
            "code_kuaidi100": "zhongtong",
            "code_kdniao": "ZTO",
            "enabled": True,
        },
        "Yunda": {
            "name": "韵达快递",
            "api_type": "kuaidi100",
            "code_kuaidi100": "yunda",
            "code_kdniao": "Yunda",
            "enabled": True,
        },
        "EMS": {
            "name": "EMS",
            "api_type": "kuaidi100",
            "code_kuaidi100": "ems",
            "code_kdniao": "EMS",
            "enabled": True,
        },
        "JD": {
            "name": "京东物流",
            "api_type": "kuaidi100",
            "code_kuaidi100": "jingdong",
            "code_kdniao": "JD",
            "enabled": True,
        },
        "YZPY": {
            "name": "邮政平邮",
            "api_type": "kuaidi100",
            "code_kuaidi100": "youzhengguonei",
            "code_kdniao": "YZPY",
            "enabled": True,
        },
        "HHTT": {
            "name": "天天快递",
            "api_type": "kuaidi100",
            "code_kuaidi100": "tiantian",
            "code_kdniao": "HHTT",
            "enabled": True,
        },
        "DBL": {
            "name": "德邦快递",
            "api_type": "kuaidi100",
            "code_kuaidi100": "debangwuliu",
            "code_kdniao": "DBL",
            "enabled": True,
        },
    }

    # Status mapping from courier APIs to standard status
    STATUS_MAPPING = {
        "0": "pending",
        "1": "shipped",
        "2": "shipped",
        "3": "delivered",
        "4": "failed",
        "5": "returned",
        "6": "exception",
        "PICKED_UP": "shipped",
        "IN_TRANSIT": "shipped",
        "OUT_FOR_DELIVERY": "shipped",
        "DELIVERED": "delivered",
        "FAILED": "failed",
        "RETURNED": "returned",
        "EXCEPTION": "exception",
    }

    def __init__(self):
        """Initialize tracking service."""
        # TODO: Load API credentials from config
        self.kuaidi100_customer = None  # From config
        self.kuaidi100_key = None  # From config
        self.kdniao_ebusiness_id = None  # From config
        self.kdniao_app_key = None  # From config

        # HTTP client for API requests
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    def get_supported_couriers(self) -> List[Dict[str, Any]]:
        """
        Get list of supported courier companies.

        Returns:
            List of courier configurations with code, name, and enabled status
        """
        return [
            {
                "code": code,
                "name": config["name"],
                "enabled": config["enabled"],
            }
            for code, config in self.SUPPORTED_COURIERS.items()
            if config["enabled"]
        ]

    async def fetch_tracking_info(
        self, courier_code: str, tracking_number: str
    ) -> TrackingInfo:
        """
        Fetch tracking information from courier API.

        Args:
            courier_code: Courier company code
            tracking_number: Tracking number

        Returns:
            TrackingInfo with current status and events

        Raises:
            ValidationException: If parameters are invalid
            BusinessException: If API call fails
        """
        # Validate input
        if not courier_code:
            raise ValidationException("快递公司代码不能为空")
        if not tracking_number:
            raise ValidationException("物流单号不能为空")

        # Check if courier is supported
        if courier_code not in self.SUPPORTED_COURIERS:
            raise BusinessException(f"不支持的快递公司: {courier_code}")

        courier_config = self.SUPPORTED_COURIERS[courier_code]
        if not courier_config["enabled"]:
            raise BusinessException(f"快递公司暂不可用: {courier_config['name']}")

        try:
            # Call courier API
            response_data = await self._call_courier_api(
                courier_code, tracking_number
            )

            # Parse response
            tracking_info = await self.parse_tracking_response(
                courier_code, response_data
            )

            logger.info(
                f"Fetched tracking for {tracking_number}: {tracking_info.current_status}"
            )
            return tracking_info

        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching tracking for {tracking_number}: {e}")
            raise BusinessException("物流API调用超时", code="TRACKING_TIMEOUT")

        except httpx.HTTPStatusError as e:
            logger.error(f"API error fetching tracking for {tracking_number}: {e}")
            raise BusinessException("物流API调用失败", code="TRACKING_API_ERROR")

        except Exception as e:
            logger.error(f"Error fetching tracking for {tracking_number}: {e}")
            raise BusinessException("获取物流信息失败", code="TRACKING_FETCH_FAILED")

    async def _call_courier_api(
        self, courier_code: str, tracking_number: str
    ) -> Dict[str, Any]:
        """
        Call appropriate courier API based on configuration.

        Args:
            courier_code: Courier company code
            tracking_number: Tracking number

        Returns:
            Raw API response data
        """
        courier_config = self.SUPPORTED_COURIERS[courier_code]
        api_type = courier_config["api_type"]

        if api_type == "kuaidi100":
            return await self._call_kuaidi100_api(
                courier_config["code_kuaidi100"], tracking_number
            )
        elif api_type == "kdniao":
            return await self._call_kdniao_api(
                courier_config["code_kdniao"], tracking_number
            )
        else:
            raise BusinessException(f"不支持的API类型: {api_type}")

    async def _call_kuaidi100_api(
        self, courier_code: str, tracking_number: str
    ) -> Dict[str, Any]:
        """
        Call Kuaidi100 API.

        Args:
            courier_code: Kuaidi100 courier code
            tracking_number: Tracking number

        Returns:
            API response data
        """
        # TODO: Implement actual Kuaidi100 API call
        # For now, return mock data
        url = "https://poll.kuaidi100.com/poll/query.do"

        # Mock response - replace with actual API call
        # params = {
        #     "customer": self.kuaidi100_customer,
        #     "param": json.dumps({"com": courier_code, "num": tracking_number}),
        #     "sign": self._generate_kuaidi100_sign(...),
        # }

        # For testing, return mock data
        return {
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

    async def _call_kdniao_api(
        self, courier_code: str, tracking_number: str
    ) -> Dict[str, Any]:
        """
        Call KDNiao API.

        Args:
            courier_code: KDNiao courier code
            tracking_number: Tracking number

        Returns:
            API response data
        """
        # TODO: Implement actual KDNiao API call
        url = "https://api.kdniao.com/api/OOrderService"

        # Mock response - replace with actual API call
        return {
            "success": True,
            "state": "0",
            "traces": [
                {
                    "AcceptTime": "2024-02-20 10:00:00",
                    "AcceptStation": "Package picked up",
                    "Remark": "Shenzhen",
                },
                {
                    "AcceptTime": "2024-02-20 22:00:00",
                    "AcceptStation": "Package in transit",
                    "Remark": "Guangzhou",
                },
            ],
        }

    async def parse_tracking_response(
        self, courier_code: str, response_data: Dict[str, Any]
    ) -> TrackingInfo:
        """
        Parse courier API response into standard TrackingInfo format.

        Args:
            courier_code: Courier company code
            response_data: Raw API response data

        Returns:
            Standardized TrackingInfo

        Raises:
            BusinessException: If parsing fails
        """
        courier_config = self.SUPPORTED_COURIERS.get(courier_code)
        if not courier_config:
            raise BusinessException(f"不支持的快递公司: {courier_code}")

        api_type = courier_config["api_type"]

        try:
            if api_type == "kuaidi100":
                return self._parse_kuaidi100_response(courier_code, response_data)
            elif api_type == "kdniao":
                return self._parse_kdniao_response(courier_code, response_data)
            else:
                raise BusinessException(f"不支持的API类型: {api_type}")

        except BusinessException:
            # Re-raise business exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Error parsing tracking response: {e}")
            raise BusinessException("物流信息解析失败", code="TRACKING_PARSE_FAILED")

    def _parse_kuaidi100_response(
        self, courier_code: str, response_data: Dict[str, Any]
    ) -> TrackingInfo:
        """Parse Kuaidi100 API response."""
        # Validate response has required fields
        if "state" not in response_data and "data" not in response_data:
            raise BusinessException("物流信息解析失败: 缺少必要字段", code="TRACKING_PARSE_FAILED")

        # Map status code
        state_code = response_data.get("state", "0")
        current_status = self.STATUS_MAPPING.get(
            state_code, "pending"
        )

        # Parse events
        events_data = response_data.get("data", [])
        events = []

        for event in events_data:
            try:
                # Parse timestamp
                time_str = event.get("time", "")
                timestamp = self._parse_timestamp(time_str)

                event_schema = TrackingEventSchema(
                    status=current_status,
                    description=event.get("context", ""),
                    location=event.get("location", ""),
                    timestamp=timestamp,
                )
                events.append(event_schema)
            except Exception as e:
                logger.warning(f"Error parsing tracking event: {e}")
                continue

        return TrackingInfo(
            tracking_number=response_data.get("nu", ""),
            courier_code=courier_code,
            current_status=current_status,
            estimated_delivery=None,  # Kuaidi100 doesn't provide ETA
            events=events,
        )

    def _parse_kdniao_response(
        self, courier_code: str, response_data: Dict[str, Any]
    ) -> TrackingInfo:
        """Parse KDNiao API response."""
        # Map status code
        state_code = response_data.get("state", "0")
        current_status = self.STATUS_MAPPING.get(
            state_code, "pending"
        )

        # Parse events
        traces_data = response_data.get("traces", [])
        events = []

        for trace in traces_data:
            try:
                # Parse timestamp
                time_str = trace.get("AcceptTime", "")
                timestamp = self._parse_timestamp(time_str)

                event_schema = TrackingEventSchema(
                    status=current_status,
                    description=trace.get("AcceptStation", ""),
                    location=trace.get("Remark", ""),
                    timestamp=timestamp,
                )
                events.append(event_schema)
            except Exception as e:
                logger.warning(f"Error parsing tracking event: {e}")
                continue

        return TrackingInfo(
            tracking_number=response_data.get("LogisticCode", ""),
            courier_code=courier_code,
            current_status=current_status,
            estimated_delivery=None,
            events=events,
        )

    def _parse_timestamp(self, time_str: str) -> datetime:
        """Parse timestamp string to datetime object."""
        try:
            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            # If all formats fail, return current time
            return datetime.utcnow()
        except Exception:
            return datetime.utcnow()

    async def update_shipment_tracking(
        self, db: AsyncSession, shipment_id: int, tracking_info: TrackingInfo
    ) -> Shipment:
        """
        Update shipment with latest tracking information.

        Args:
            db: Database session
            shipment_id: Shipment ID
            tracking_info: Latest tracking information

        Returns:
            Updated shipment

        Raises:
            BusinessException: If shipment not found
        """
        # Fetch shipment
        result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
        shipment = result.scalar_one_or_none()

        if not shipment:
            raise BusinessException(f"物流记录不存在: {shipment_id}")

        # Update status (direct string assignment)
        shipment.status = tracking_info.current_status

        # Update timestamps
        if tracking_info.current_status == TrackingStatus.SHIPPED and not shipment.shipped_at:
            shipment.shipped_at = datetime.utcnow()
        elif tracking_info.current_status == TrackingStatus.DELIVERED and not shipment.delivered_at:
            shipment.delivered_at = datetime.utcnow()

        # Save tracking events
        for event in tracking_info.events:
            # Check if event already exists
            existing_event = await db.execute(
                select(TrackingEvent).where(
                    and_(
                        TrackingEvent.shipment_id == shipment_id,
                        TrackingEvent.timestamp == event.timestamp,
                        TrackingEvent.description == event.description,
                    )
                )
            )
            if not existing_event.scalar_one_or_none():
                # Create new tracking event
                tracking_event = TrackingEvent(
                    shipment_id=shipment_id,
                    status=event.status,
                    description=event.description,
                    location=event.location,
                    timestamp=event.timestamp,
                )
                db.add(tracking_event)

        await db.commit()
        await db.refresh(shipment)

        logger.info(f"Updated shipment {shipment_id} tracking to {tracking_info.current_status}")
        return shipment

    async def batch_update_tracking(
        self, db: AsyncSession
    ) -> Dict[str, int]:
        """
        Batch update tracking for all pending/in-transit shipments.

        Args:
            db: Database session

        Returns:
            Dictionary with total, updated, and failed counts
        """
        # Find shipments that need updates
        statuses_to_update = [
            TrackingStatus.PENDING,
            TrackingStatus.SHIPPED,
            TrackingStatus.IN_TRANSIT,
        ]

        result = await db.execute(
            select(Shipment).where(
                and_(
                    Shipment.courier_code.isnot(None),
                    Shipment.tracking_number.isnot(None),
                    Shipment.status.in_(statuses_to_update),
                )
            )
        )
        shipments = result.scalars().all()

        total = len(shipments)
        updated = 0
        failed = 0

        logger.info(f"Starting batch update for {total} shipments")

        for shipment in shipments:
            try:
                # Fetch latest tracking
                tracking_info = await self.fetch_tracking_info(
                    shipment.courier_code, shipment.tracking_number
                )

                # Update shipment
                await self.update_shipment_tracking(db, shipment.id, tracking_info)
                updated += 1

            except Exception as e:
                logger.error(
                    f"Failed to update shipment {shipment.id}: {e}",
                    exc_info=True,
                )
                failed += 1
                continue

        logger.info(f"Batch update complete: {updated} updated, {failed} failed")

        return {
            "total": total,
            "updated": updated,
            "failed": failed,
        }
