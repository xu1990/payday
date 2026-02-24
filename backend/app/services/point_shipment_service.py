"""
积分订单物流服务 - Point Shipment Service

专门处理积分订单的物流发货、跟踪和管理：
1. create_shipment - 创建发货记录（仅限积分订单）
2. list_shipments - 获取积分订单发货列表
3. get_shipment - 获取发货记录
4. update_shipment - 更新发货信息和状态
5. get_tracking_info - 获取物流跟踪信息

关键特性：
- 仅支持积分订单（payment_method = 'points'）
- 防止重复发货
- 物流状态同步（自动更新订单状态）
- 分页查询支持
- 状态和物流公司过滤
- 业务规则验证（订单状态、物流公司验证）
"""
import logging
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.shipping import OrderShipment, CourierCompany
from app.core.exceptions import NotFoundException, BusinessException, ValidationException

logger = logging.getLogger(__name__)


class PointShipmentService:
    """
    积分订单物流服务

    专门处理积分订单的物流发货、跟踪和管理。

    Example:
        ```python
        service = PointShipmentService()

        # 创建发货记录
        shipment = await service.create_shipment(
            db=db,
            order_id="order_123",
            courier_code="SF",
            tracking_number="SF1234567890"
        )

        # 获取发货列表
        shipments = await service.list_shipments(
            db=db,
            skip=0,
            limit=10,
            status="pending"
        )

        # 更新物流信息
        updated = await service.update_shipment(
            db=db,
            shipment_id="shipment_123",
            tracking_number="SF1234567891",
            status="in_transit"
        )

        # 获取物流跟踪信息
        tracking = await service.get_tracking_info(db=db, shipment_id="shipment_123")
        ```
    """

    # Valid shipment statuses
    VALID_SHIPMENT_STATUSES = ["pending", "picked_up", "in_transit", "delivered", "failed"]

    # Valid payment methods for point shipments
    VALID_PAYMENT_METHODS = ["points", "hybrid"]

    # Valid statuses for shipment creation
    CREATE_ALLOWED_STATUSES = ["paid"]

    async def create_shipment(
        self,
        db: AsyncSession,
        order_id: str,
        courier_code: str,
        tracking_number: str
    ) -> OrderShipment:
        """
        创建积分订单发货记录

        流程：
        1. 验证订单存在且是积分订单
        2. 验证订单已支付
        3. 检查订单未发货（防止重复发货）
        4. 验证物流公司存在
        5. 创建发货记录
        6. 更新订单状态为shipped

        Args:
            db: 数据库session
            order_id: 订单ID
            courier_code: 物流公司代码
            tracking_number: 物流单号

        Returns:
            OrderShipment: 发货记录对象

        Raises:
            NotFoundException: 订单或物流公司不存在
            BusinessException: 订单类型错误、未支付、已发货
            ValidationException: 无效的物流状态
        """
        try:
            # 1. 获取订单
            order = await self._get_order_by_id(db, order_id)
            if not order:
                raise NotFoundException("订单不存在")

            # 2. 验证订单类型是积分订单
            if order.payment_method not in self.VALID_PAYMENT_METHODS:
                raise BusinessException(
                    "该订单类型不能使用积分订单物流服务",
                    code="INVALID_ORDER_TYPE",
                    details={
                        "payment_method": order.payment_method,
                        "allowed_methods": self.VALID_PAYMENT_METHODS
                    }
                )

            # 3. 验证订单状态
            if order.payment_status not in ["paid"]:
                raise BusinessException(
                    "订单未支付，不能发货",
                    code="ORDER_NOT_PAID"
                )

            # 4. 检查是否已发货
            existing_shipment = await self._get_shipment_by_order(db, order_id)
            if existing_shipment:
                raise BusinessException(
                    "订单已发货",
                    code="ALREADY_SHIPPED"
                )

            # 5. 获取物流公司信息
            courier = await self._get_courier_by_code(db, courier_code)
            if not courier:
                raise NotFoundException("物流公司不存在")

            # 6. 创建发货记录
            shipment = OrderShipment(
                order_id=order_id,
                courier_code=courier.code,
                courier_name=courier.name,
                tracking_number=tracking_number,
                status="pending",
                shipped_at=datetime.utcnow(),
                tracking_info=None
            )

            db.add(shipment)
            await db.flush()

            # 7. 更新订单状态
            order.status = "shipped"
            order.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(shipment)

            logger.info(
                f"Point shipment created for order {order_id}, "
                f"courier={courier_code}, tracking={tracking_number}"
            )

            return shipment

        except (NotFoundException, BusinessException, ValidationException):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating point shipment for order {order_id}: {e}")
            raise BusinessException(
                "创建积分订单发货记录失败",
                code="POINT_SHIPMENT_CREATE_FAILED"
            )

    async def list_shipments(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        courier_code: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[OrderShipment]:
        """
        获取积分订单发货列表

        Args:
            db: 数据库session
            skip: 跳过数量
            limit: 返回数量限制
            status: 发货状态过滤
            courier_code: 物流公司代码过滤
            user_id: 用户ID过滤（权限控制）

        Returns:
            List[OrderShipment]: 发货记录列表

        Raises:
            ValidationException: 无效的分页参数
        """
        try:
            # Validate pagination
            if skip < 0 or limit <= 0:
                raise ValidationException(
                    "分页参数无效",
                    details={"skip": skip, "limit": limit}
                )

            # Build query
            query = select(OrderShipment).join(Order)

            # Filter by status if provided
            if status:
                if status not in self.VALID_SHIPMENT_STATUSES:
                    raise ValidationException(
                        "无效的发货状态",
                        details={
                            "status": status,
                            "valid_statuses": self.VALID_SHIPMENT_STATUSES
                        }
                    )
                query = query.where(OrderShipment.status == status)

            # Filter by courier if provided
            if courier_code:
                query = query.where(OrderShipment.courier_code == courier_code)

            # Filter by user if provided
            if user_id:
                query = query.where(Order.user_id == user_id)

            # Order by creation time
            query = query.order_by(desc(OrderShipment.created_at))

            # Apply pagination (+1 to check if more exist)
            query = query.offset(skip).limit(limit + 1)

            result = await db.execute(query)
            shipments = list(result.scalars().all())

            # Check if we have more results than limit
            has_more = len(shipments) > limit
            if has_more:
                shipments = shipments[:limit]

            logger.info(
                f"Listed {len(shipments)} shipments "
                f"(skip={skip}, limit={limit}, has_more={has_more})"
            )

            return shipments

        except (ValidationException):
            raise
        except Exception as e:
            logger.error(f"Error listing shipments: {e}")
            raise BusinessException(
                "获取发货列表失败",
                code="LIST_SHIPMENTS_FAILED"
            )

    async def get_shipment(
        self,
        db: AsyncSession,
        shipment_id: str
    ) -> OrderShipment:
        """
        获取发货记录

        Args:
            db: 数据库session
            shipment_id: 发货记录ID

        Returns:
            OrderShipment: 发货记录对象

        Raises:
            NotFoundException: 发货记录不存在
        """
        try:
            shipment = await self._get_shipment_by_id(db, shipment_id)

            if not shipment:
                raise NotFoundException("发货记录不存在")

            return shipment

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting shipment {shipment_id}: {e}")
            raise

    async def update_shipment(
        self,
        db: AsyncSession,
        shipment_id: str,
        tracking_number: Optional[str] = None,
        status: Optional[str] = None,
        tracking_info: Optional[List[dict]] = None
    ) -> OrderShipment:
        """
        更新发货记录

        流程：
        1. 验证发货记录存在
        2. 更新物流信息（单号、状态、跟踪详情）
        3. 如果状态为已签收，更新订单状态
        4. 验证状态变更的有效性

        Args:
            db: 数据库session
            shipment_id: 发货记录ID
            tracking_number: 新的物流单号
            status: 新的物流状态
            tracking_info: 物流跟踪详情

        Returns:
            OrderShipment: 更新后的发货记录

        Raises:
            NotFoundException: 发货记录不存在
            ValidationException: 无效的物流状态
        """
        try:
            # 1. 获取发货记录
            shipment = await self._get_shipment_by_id(db, shipment_id)

            if not shipment:
                raise NotFoundException("发货记录不存在")

            # 2. 更新物流单号
            if tracking_number and tracking_number != shipment.tracking_number:
                shipment.tracking_number = tracking_number

            # 3. 更新状态（如果提供）
            if status:
                if status not in self.VALID_SHIPMENT_STATUSES:
                    raise ValidationException(
                        "无效的物流状态",
                        details={"valid_statuses": self.VALID_SHIPMENT_STATUSES}
                    )

                # 验证状态变更有效性
                self._validate_status_transition(shipment.status, status)

                shipment.status = status

                # 4. 如果已签收，记录签收时间
                if status == "delivered" and not shipment.delivered_at:
                    shipment.delivered_at = datetime.utcnow()

            # 5. 更新物流跟踪信息
            if tracking_info:
                shipment.tracking_info = tracking_info

            # 6. 更新订单状态（如果状态变更）
            if status:
                order = await self._get_order_by_id(db, shipment.order_id)
                if order:
                    if status == "delivered":
                        order.status = "delivered"
                    elif status in ["picked_up", "in_transit"]:
                        order.status = "shipped"

                    order.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(shipment)

            logger.info(
                f"Shipment {shipment_id} updated "
                f"(tracking={shipment.tracking_number}, status={shipment.status})"
            )

            return shipment

        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating shipment {shipment_id}: {e}")
            raise BusinessException(
                "更新发货记录失败",
                code="UPDATE_SHIPMENT_FAILED"
            )

    async def get_tracking_info(
        self,
        db: AsyncSession,
        shipment_id: str
    ) -> List[dict]:
        """
        获取物流跟踪信息

        Args:
            db: 数据库session
            shipment_id: 发货记录ID

        Returns:
            List[dict]: 物流跟踪详情列表，如果不存在则返回空列表

        Raises:
            NotFoundException: 发货记录不存在
        """
        try:
            # 1. 获取发货记录
            shipment = await self._get_shipment_by_id(db, shipment_id)

            if not shipment:
                raise NotFoundException("发货记录不存在")

            # 2. 返回跟踪信息，如果不存在则返回空列表
            return shipment.tracking_info or []

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting tracking info for shipment {shipment_id}: {e}")
            raise

    # Private helper methods

    async def _get_order_by_id(self, db: AsyncSession, order_id: str) -> Optional[Order]:
        """根据ID获取订单"""
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def _get_shipment_by_id(self, db: AsyncSession, shipment_id: str) -> Optional[OrderShipment]:
        """根据ID获取发货记录"""
        result = await db.execute(
            select(OrderShipment).where(OrderShipment.id == shipment_id)
        )
        return result.scalar_one_or_none()

    async def _get_shipment_by_order(self, db: AsyncSession, order_id: str) -> Optional[OrderShipment]:
        """根据订单ID获取发货记录"""
        result = await db.execute(
            select(OrderShipment).where(OrderShipment.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def _get_courier_by_code(self, db: AsyncSession, code: str) -> Optional[CourierCompany]:
        """根据代码获取物流公司"""
        code = code.upper().strip()
        result = await db.execute(
            select(CourierCompany)
            .where(CourierCompany.code == code)
            .where(CourierCompany.is_active == True)
        )
        return result.scalar_one_or_none()

    def _validate_status_transition(self, current_status: str, new_status: str):
        """验证状态变更的有效性"""
        # Simple state machine validation
        status_transitions = {
            "pending": ["picked_up", "failed"],
            "picked_up": ["in_transit", "failed"],
            "in_transit": ["delivered", "failed"],
            "delivered": [],  # Final state
            "failed": []  # Final state
        }

        if current_status not in status_transitions:
            raise ValidationException(
                f"无效的当前状态: {current_status}"
            )

        if new_status not in status_transitions[current_status]:
            allowed = ", ".join(status_transitions[current_status])
            raise ValidationException(
                f"不能从 '{current_status}' 变更到 '{new_status}'",
                details={
                    "current_status": current_status,
                    "allowed_transitions": status_transitions[current_status]
                }
            )