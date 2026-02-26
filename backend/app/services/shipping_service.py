"""
Shipping Service - 物流服务

处理订单发货、物流跟踪、退货退款等功能：
1. create_shipment - 创建发货记录
2. get_shipment - 获取发货记录
3. update_tracking_status - 更新物流状态
4. create_return_request - 创建退货申请
5. approve_return - 审批通过退货
6. reject_return - 拒绝退货
7. process_refund - 处理退款
8. get_returns_by_order - 获取订单退货列表

关键特性：
- 订单状态校验（只有已支付订单才能发货）
- 退货权限验证（只能退货自己的订单）
- 退货状态机管理（申请→审批→退款→完成）
- 物流状态同步（自动更新订单状态）
- 业务规则验证（未签收不能退货、状态不正确不能操作）
"""

"""
ShippingTemplateService - 运费模板服务

管理运费模板和区域配置：
1. create_template - 创建运费模板
2. list_templates - 列出运费模板
3. get_template - 获取运费模板
4. update_template - 更新运费模板
5. delete_template - 删除运费模板
6. create_region - 创建运费模板区域
7. list_regions - 列出运费模板区域
8. get_region - 获取运费模板区域
9. update_region - 更新运费模板区域
10. delete_region - 删除运费模板区域

关键特性：
- 支持重量、数量、固定三种计费方式
- 支持区域差异化定价
- 支持包邮门槛设置
- 支持预计送达时间设置
- 软删除机制保护数据完整性
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.order import Order, OrderItem
from app.models.shipping import (CourierCompany, OrderReturn, OrderShipment, ShippingTemplate,
                                 ShippingTemplateRegion)
from app.schemas.shipping import (ShippingTemplateCreate, ShippingTemplateRegionCreate,
                                  ShippingTemplateRegionResponse, ShippingTemplateRegionUpdate,
                                  ShippingTemplateResponse, ShippingTemplateUpdate)
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ShippingService:
    """
    物流服务

    处理订单发货、物流跟踪和退货退款的完整流程。

    Example:
        ```python
        service = ShippingService()

        # 创建发货记录
        shipment = await service.create_shipment(
            db=db,
            order_id="order_123",
            courier_code="SF",
            tracking_number="SF1234567890"
        )

        # 更新物流状态
        shipment = await service.update_tracking_status(
            db=db,
            shipment_id="shipment_123",
            status="in_transit",
            tracking_info=[...]
        )

        # 创建退货申请
        return_request = await service.create_return_request(
            db=db,
            order_id="order_123",
            order_item_id="item_123",
            reason="quality_issue",
            return_type="refund_only"
        )

        # 审批退货
        approved = await service.approve_return(
            db=db,
            return_id="return_123",
            admin_id="admin_123"
        )

        # 处理退款
        refunded = await service.process_refund(
            db=db,
            return_id="return_123",
            refund_amount=Decimal("100.00")
        )
        ```
    """

    # Valid shipment statuses
    VALID_SHIPMENT_STATUSES = ["pending", "picked_up", "in_transit", "delivered", "failed"]

    # Valid return reasons
    VALID_RETURN_REASONS = [
        "quality_issue",
        "damaged",
        "wrong_item",
        "not_as_described",
        "no_longer_needed",
        "other"
    ]

    # Valid return types
    VALID_RETURN_TYPES = ["refund_only", "replace", "return_and_refund"]

    # Valid return statuses for approval
    RETURN_STATUSES_FOR_APPROVAL = ["requested"]

    # Valid return statuses for rejection
    RETURN_STATUSES_FOR_REJECTION = ["requested", "approved"]

    # Valid return statuses for refund
    RETURN_STATUSES_FOR_REFUND = ["approved"]

    async def create_shipment(
        self,
        db: AsyncSession,
        order_id: str,
        courier_code: str,
        tracking_number: str
    ) -> OrderShipment:
        """
        创建发货记录

        流程：
        1. 验证订单存在且已支付
        2. 检查订单未发货（防止重复发货）
        3. 验证物流公司存在
        4. 创建发货记录
        5. 更新订单状态为shipped

        Args:
            db: 数据库session
            order_id: 订单ID
            courier_code: 物流公司代码
            tracking_number: 物流单号

        Returns:
            OrderShipment: 发货记录对象

        Raises:
            NotFoundException: 订单或物流公司不存在
            BusinessException: 订单未支付、已发货
        """
        try:
            # 1. 获取订单
            order = await self._get_order_by_id(db, order_id)
            if not order:
                raise NotFoundException("订单不存在")

            # 2. 验证订单状态
            if order.payment_status != "paid":
                raise BusinessException(
                    "订单未支付，不能发货",
                    code="ORDER_NOT_PAID"
                )

            # 3. 检查是否已发货
            existing_shipment = await self._get_shipment_by_order(db, order_id)
            if existing_shipment:
                raise BusinessException(
                    "订单已发货",
                    code="ALREADY_SHIPPED"
                )

            # 4. 获取物流公司信息
            courier = await self._get_courier_by_code(db, courier_code)
            if not courier:
                raise NotFoundException("物流公司不存在")

            # 5. 创建发货记录
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

            # 6. 更新订单状态
            order.status = "shipped"
            order.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(shipment)

            logger.info(
                f"Shipment created for order {order_id}, "
                f"courier={courier_code}, tracking={tracking_number}"
            )

            return shipment

        except (NotFoundException, BusinessException):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating shipment for order {order_id}: {e}")
            raise BusinessException(
                "创建发货记录失败",
                code="SHIPMENT_CREATE_FAILED"
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

    async def update_tracking_status(
        self,
        db: AsyncSession,
        shipment_id: str,
        status: str,
        tracking_info: Optional[List[dict]] = None
    ) -> OrderShipment:
        """
        更新物流状态

        流程：
        1. 验证发货记录存在
        2. 验证状态有效
        3. 更新物流状态和跟踪信息
        4. 如果状态为已签收，更新订单状态

        Args:
            db: 数据库session
            shipment_id: 发货记录ID
            status: 物流状态
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

            # 2. 验证状态
            if status not in self.VALID_SHIPMENT_STATUSES:
                raise ValidationException(
                    "无效的物流状态",
                    details={"valid_statuses": self.VALID_SHIPMENT_STATUSES}
                )

            # 3. 更新发货记录
            shipment.status = status
            if tracking_info:
                shipment.tracking_info = tracking_info

            # 4. 如果已签收，记录签收时间
            if status == "delivered" and not shipment.delivered_at:
                shipment.delivered_at = datetime.utcnow()

            # 5. 更新订单状态
            order = await self._get_order_by_id(db, shipment.order_id)
            if order:
                if status == "delivered":
                    order.status = "delivered"
                elif status == "in_transit":
                    order.status = "shipped"

                order.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(shipment)

            logger.info(
                f"Shipment {shipment_id} status updated to {status}"
            )

            return shipment

        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating tracking status for shipment {shipment_id}: {e}")
            raise BusinessException(
                "更新物流状态失败",
                code="TRACKING_UPDATE_FAILED"
            )

    async def create_return_request(
        self,
        db: AsyncSession,
        order_id: str,
        order_item_id: str,
        reason: str,
        return_type: str,
        description: Optional[str] = None,
        images: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> OrderReturn:
        """
        创建退货申请

        流程：
        1. 验证订单存在
        2. 验证订单项存在
        3. 验证订单所有权（如果提供user_id）
        4. 验证订单已签收
        5. 验证退货原因和类型有效
        6. 创建退货申请

        Args:
            db: 数据库session
            order_id: 订单ID
            order_item_id: 订单项ID
            reason: 退货原因
            return_type: 退货类型
            description: 退货说明
            images: 凭证图片
            user_id: 用户ID（用于权限验证）

        Returns:
            OrderReturn: 退货申请对象

        Raises:
            NotFoundException: 订单或订单项不存在
            BusinessException: 无权访问、订单未签收
            ValidationException: 无效的退货原因或类型
        """
        try:
            # 1. 获取订单
            order = await self._get_order_by_id(db, order_id)
            if not order:
                raise NotFoundException("订单不存在")

            # 2. 获取订单项
            order_item = await self._get_order_item_by_id(db, order_item_id)
            if not order_item:
                raise NotFoundException("订单项不存在")

            # 3. 验证订单项属于该订单
            if order_item.order_id != order_id:
                raise ValidationException("订单项不属于该订单")

            # 4. 验证订单所有权（如果提供user_id）
            if user_id and order.user_id != user_id:
                raise BusinessException(
                    "无权访问此订单",
                    code="FORBIDDEN"
                )

            # 5. 验证订单状态
            if order.status not in ["delivered", "completed"]:
                raise BusinessException(
                    "订单未签收，不能退货",
                    code="ORDER_NOT_DELIVERED"
                )

            # 6. 验证退货原因
            if reason not in self.VALID_RETURN_REASONS:
                raise ValidationException(
                    "无效的退货原因",
                    details={"valid_reasons": self.VALID_RETURN_REASONS}
                )

            # 7. 验证退货类型
            if return_type not in self.VALID_RETURN_TYPES:
                raise ValidationException(
                    "无效的退货类型",
                    details={"valid_types": self.VALID_RETURN_TYPES}
                )

            # 8. 创建退货申请
            return_request = OrderReturn(
                order_id=order_id,
                order_item_id=order_item_id,
                return_reason=reason,
                return_description=description,
                images=images,
                return_type=return_type,
                status="requested",
                requested_at=datetime.utcnow()
            )

            db.add(return_request)
            await db.commit()
            await db.refresh(return_request)

            logger.info(
                f"Return request created for order {order_id}, "
                f"item {order_item_id}, reason={reason}, type={return_type}"
            )

            return return_request

        except (NotFoundException, BusinessException, ValidationException):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating return request for order {order_id}: {e}")
            raise BusinessException(
                "创建退货申请失败",
                code="RETURN_CREATE_FAILED"
            )

    async def approve_return(
        self,
        db: AsyncSession,
        return_id: str,
        admin_id: str,
        notes: Optional[str] = None
    ) -> OrderReturn:
        """
        审批通过退货

        流程：
        1. 验证退货记录存在
        2. 验证状态允许审批
        3. 更新退货状态为approved
        4. 记录审批时间和管理员信息

        Args:
            db: 数据库session
            return_id: 退货记录ID
            admin_id: 管理员ID
            notes: 管理员备注

        Returns:
            OrderReturn: 更新后的退货记录

        Raises:
            NotFoundException: 退货记录不存在
            BusinessException: 状态不正确
        """
        try:
            # 1. 获取退货记录
            return_request = await self._get_return_by_id(db, return_id)

            if not return_request:
                raise NotFoundException("退货记录不存在")

            # 2. 验证状态
            if return_request.status not in self.RETURN_STATUSES_FOR_APPROVAL:
                raise BusinessException(
                    "退货状态不正确，不能审批",
                    code="INVALID_RETURN_STATUS",
                    details={
                        "current_status": return_request.status,
                        "expected_statuses": self.RETURN_STATUSES_FOR_APPROVAL
                    }
                )

            # 3. 更新状态
            return_request.status = "approved"
            return_request.admin_id = admin_id
            return_request.admin_notes = notes
            return_request.approved_at = datetime.utcnow()

            await db.commit()
            await db.refresh(return_request)

            logger.info(f"Return {return_id} approved by admin {admin_id}")

            return return_request

        except (NotFoundException, BusinessException):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error approving return {return_id}: {e}")
            raise BusinessException(
                "审批退货失败",
                code="RETURN_APPROVE_FAILED"
            )

    async def reject_return(
        self,
        db: AsyncSession,
        return_id: str,
        admin_id: str,
        notes: Optional[str] = None
    ) -> OrderReturn:
        """
        拒绝退货

        流程：
        1. 验证退货记录存在
        2. 验证状态允许拒绝
        3. 更新退货状态为rejected
        4. 记录管理员信息

        Args:
            db: 数据库session
            return_id: 退货记录ID
            admin_id: 管理员ID
            notes: 拒绝原因

        Returns:
            OrderReturn: 更新后的退货记录

        Raises:
            NotFoundException: 退货记录不存在
            BusinessException: 状态不正确
        """
        try:
            # 1. 获取退货记录
            return_request = await self._get_return_by_id(db, return_id)

            if not return_request:
                raise NotFoundException("退货记录不存在")

            # 2. 验证状态
            if return_request.status not in self.RETURN_STATUSES_FOR_REJECTION:
                raise BusinessException(
                    "退货状态不正确，不能拒绝",
                    code="INVALID_RETURN_STATUS",
                    details={
                        "current_status": return_request.status,
                        "expected_statuses": self.RETURN_STATUSES_FOR_REJECTION
                    }
                )

            # 3. 更新状态
            return_request.status = "rejected"
            return_request.admin_id = admin_id
            return_request.admin_notes = notes

            await db.commit()
            await db.refresh(return_request)

            logger.info(f"Return {return_id} rejected by admin {admin_id}")

            return return_request

        except (NotFoundException, BusinessException):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error rejecting return {return_id}: {e}")
            raise BusinessException(
                "拒绝退货失败",
                code="RETURN_REJECT_FAILED"
            )

    async def process_refund(
        self,
        db: AsyncSession,
        return_id: str,
        refund_amount: Decimal,
        transaction_id: Optional[str] = None
    ) -> OrderReturn:
        """
        处理退款

        流程：
        1. 验证退货记录存在
        2. 验证状态允许退款
        3. 验证退款金额有效
        4. 更新退货状态为completed
        5. 记录退款金额和交易ID

        Args:
            db: 数据库session
            return_id: 退货记录ID
            refund_amount: 退款金额
            transaction_id: 退款交易ID

        Returns:
            OrderReturn: 更新后的退货记录

        Raises:
            NotFoundException: 退货记录不存在
            BusinessException: 状态不正确
            ValidationException: 退款金额无效
        """
        try:
            # 1. 获取退货记录
            return_request = await self._get_return_by_id(db, return_id)

            if not return_request:
                raise NotFoundException("退货记录不存在")

            # 2. 验证状态
            if return_request.status not in self.RETURN_STATUSES_FOR_REFUND:
                raise BusinessException(
                    "退货状态不正确，不能退款",
                    code="INVALID_RETURN_STATUS",
                    details={
                        "current_status": return_request.status,
                        "expected_statuses": self.RETURN_STATUSES_FOR_REFUND
                    }
                )

            # 3. 验证退款金额
            if refund_amount <= 0:
                raise ValidationException(
                    "退款金额必须大于0",
                    details={"refund_amount": str(refund_amount)}
                )

            # 4. 更新退货记录
            return_request.status = "completed"
            return_request.refund_amount = refund_amount
            return_request.refund_transaction_id = transaction_id
            return_request.completed_at = datetime.utcnow()

            # 5. 更新订单状态（如果全额退款）
            order = await self._get_order_by_id(db, return_request.order_id)
            if order:
                order.status = "refunded"
                order.payment_status = "refunded"
                order.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(return_request)

            logger.info(
                f"Return {return_id} refunded, amount={refund_amount}, "
                f"transaction_id={transaction_id}"
            )

            return return_request

        except (NotFoundException, BusinessException, ValidationException):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing refund for return {return_id}: {e}")
            raise BusinessException(
                "处理退款失败",
                code="REFUND_PROCESS_FAILED"
            )

    async def get_returns_by_order(
        self,
        db: AsyncSession,
        order_id: str
    ) -> List[OrderReturn]:
        """
        获取订单的所有退货记录

        Args:
            db: 数据库session
            order_id: 订单ID

        Returns:
            List[OrderReturn]: 退货记录列表

        Raises:
            NotFoundException: 订单不存在
        """
        try:
            # 验证订单存在
            order = await self._get_order_by_id(db, order_id)
            if not order:
                raise NotFoundException("订单不存在")

            # 查询退货记录
            result = await db.execute(
                select(OrderReturn)
                .where(OrderReturn.order_id == order_id)
                .order_by(OrderReturn.requested_at.desc())
            )
            returns = result.scalars().all()

            return list(returns) if returns else []

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting returns for order {order_id}: {e}")
            raise

    # Private helper methods

    async def _get_order_by_id(self, db: AsyncSession, order_id: str) -> Optional[Order]:
        """根据ID获取订单"""
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def _get_order_item_by_id(self, db: AsyncSession, item_id: str) -> Optional[OrderItem]:
        """根据ID获取订单项"""
        result = await db.execute(
            select(OrderItem).where(OrderItem.id == item_id)
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

    async def _get_return_by_id(self, db: AsyncSession, return_id: str) -> Optional[OrderReturn]:
        """根据ID获取退货记录"""
        result = await db.execute(
            select(OrderReturn).where(OrderReturn.id == return_id)
        )
        return result.scalar_one_or_none()

    async def _get_courier_by_code(self, db: AsyncSession, code: str) -> Optional[CourierCompany]:
        """根据代码获取物流公司"""
        result = await db.execute(
            select(CourierCompany)
            .where(CourierCompany.code == code)
            .where(CourierCompany.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_shipment_by_order_id(
        self,
        db: AsyncSession,
        order_id: str
    ) -> Optional[OrderShipment]:
        """
        根据订单ID获取发货记录

        Args:
            db: 数据库session
            order_id: 订单ID

        Returns:
            Optional[OrderShipment]: 发货记录对象，如果不存在则返回None
        """
        try:
            result = await db.execute(
                select(OrderShipment).where(OrderShipment.order_id == order_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting shipment by order {order_id}: {e}")
            raise


# ==================== ShippingTemplateService ====================


class ShippingTemplateService:
    """运费模板服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(self, template_data: ShippingTemplateCreate) -> ShippingTemplate:
        """创建运费模板"""
        # 验证charge_type
        valid_charge_types = ["weight", "quantity", "fixed", "volume"]
        if template_data.charge_type not in valid_charge_types:
            raise ValidationException(
                f"计费方式必须是: {', '.join(valid_charge_types)}",
                code="INVALID_CHARGE_TYPE"
            )

        # 验证free_shipping_type
        valid_free_shipping_types = ["none", "amount", "quantity", "seller"]
        if template_data.free_shipping_type not in valid_free_shipping_types:
            raise ValidationException(
                f"包邮类型必须是: {', '.join(valid_free_shipping_types)}",
                code="INVALID_FREE_SHIPPING_TYPE"
            )

        # 验证free_shipping_type与相关字段的一致性
        if template_data.free_shipping_type == "quantity" and not template_data.free_quantity:
            raise ValidationException(
                "包邮类型为按件数时，必须设置满件数包邮阈值",
                code="FREE_QUANTITY_REQUIRED"
            )

        template = ShippingTemplate(
            name=template_data.name,
            description=template_data.description,
            charge_type=template_data.charge_type,
            default_first_unit=template_data.default_first_unit,
            default_first_cost=template_data.default_first_cost,
            default_continue_unit=template_data.default_continue_unit,
            default_continue_cost=template_data.default_continue_cost,
            free_threshold=template_data.free_threshold,
            free_shipping_type=template_data.free_shipping_type,
            free_quantity=template_data.free_quantity,
            excluded_regions=template_data.excluded_regions,
            volume_unit=template_data.volume_unit,
            estimate_days_min=template_data.estimate_days_min,
            estimate_days_max=template_data.estimate_days_max,
            is_active=template_data.is_active if hasattr(template_data, 'is_active') else True
        )

        self.db.add(template)
        try:
            await self.db.commit()
            await self.db.refresh(template)
            return template
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def list_templates(self, skip: int = 0, limit: int = 100) -> List[ShippingTemplate]:
        """列出运费模板"""
        result = await self.db.execute(
            select(ShippingTemplate)
            .where(ShippingTemplate.is_active == True)
            .order_by(ShippingTemplate.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_template(self, template_id: str) -> ShippingTemplate:
        """获取运费模板"""
        result = await self.db.execute(
            select(ShippingTemplate).where(ShippingTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise NotFoundException("运费模板不存在")
        return template

    async def update_template(self, template_id: str, update_data: ShippingTemplateUpdate) -> ShippingTemplate:
        """更新运费模板"""
        template = await self.get_template(template_id)

        # 验证charge_type
        if update_data.charge_type:
            valid_charge_types = ["weight", "quantity", "fixed", "volume"]
            if update_data.charge_type not in valid_charge_types:
                raise ValidationException(
                    f"计费方式必须是: {', '.join(valid_charge_types)}",
                    code="INVALID_CHARGE_TYPE"
                )

        # 验证free_shipping_type
        if update_data.free_shipping_type:
            valid_free_shipping_types = ["none", "amount", "quantity", "seller"]
            if update_data.free_shipping_type not in valid_free_shipping_types:
                raise ValidationException(
                    f"包邮类型必须是: {', '.join(valid_free_shipping_types)}",
                    code="INVALID_FREE_SHIPPING_TYPE"
                )

        # 验证free_shipping_type与相关字段的一致性
        new_free_shipping_type = update_data.free_shipping_type or template.free_shipping_type
        new_free_quantity = update_data.free_quantity if update_data.free_quantity is not None else template.free_quantity
        if new_free_shipping_type == "quantity" and not new_free_quantity:
            raise ValidationException(
                "包邮类型为按件数时，必须设置满件数包邮阈值",
                code="FREE_QUANTITY_REQUIRED"
            )

        # 更新字段
        update_dict = update_data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(template, k, v)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete_template(self, template_id: str) -> None:
        """删除运费模板"""
        template = await self.get_template(template_id)

        # 检查是否有关联的区域配置
        region_result = await self.db.execute(
            select(func.count(ShippingTemplateRegion.id))
            .where(ShippingTemplateRegion.template_id == template_id)
        )
        region_count = region_result.scalar()

        if region_count > 0:
            # 软删除：设置为非活跃状态
            template.is_active = False
            await self.db.commit()
            raise BusinessException(
                f"模板下有{region_count}个区域配置，已将模板设置为停用状态",
                code="TEMPLATE_HAS_REGIONS"
            )

        # 硬删除
        await self.db.delete(template)
        await self.db.commit()

    async def create_region(self, template_id: str, region_data: ShippingTemplateRegionCreate) -> ShippingTemplateRegion:
        """创建运费模板区域配置"""
        # 验证模板是否存在
        template = await self.get_template(template_id)

        # 验证区域格式
        if not region_data.region_codes.strip():
            raise ValidationException("区域代码不能为空")
        if not region_data.region_names.strip():
            raise ValidationException("区域名称不能为空")

        region = ShippingTemplateRegion(
            template_id=template_id,
            region_codes=region_data.region_codes.strip(),
            region_names=region_data.region_names.strip(),
            first_unit=region_data.first_unit,
            first_cost=region_data.first_cost,
            continue_unit=region_data.continue_unit,
            continue_cost=region_data.continue_cost,
            free_threshold=region_data.free_threshold,
            free_quantity=region_data.free_quantity,
            is_excluded=region_data.is_excluded if hasattr(region_data, 'is_excluded') else False,
            is_active=region_data.is_active if hasattr(region_data, 'is_active') else True
        )

        self.db.add(region)
        try:
            await self.db.commit()
            await self.db.refresh(region)
            return region
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def list_regions(self, template_id: str, skip: int = 0, limit: int = 100) -> List[ShippingTemplateRegion]:
        """列出运费模板区域配置"""
        # 验证模板是否存在
        await self.get_template(template_id)

        result = await self.db.execute(
            select(ShippingTemplateRegion)
            .where(
                ShippingTemplateRegion.template_id == template_id,
                ShippingTemplateRegion.is_active == True
            )
            .order_by(ShippingTemplateRegion.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_region(self, region_id: str) -> ShippingTemplateRegion:
        """获取运费模板区域配置"""
        result = await self.db.execute(
            select(ShippingTemplateRegion).where(ShippingTemplateRegion.id == region_id)
        )
        region = result.scalar_one_or_none()
        if not region:
            raise NotFoundException("运费模板区域配置不存在")
        return region

    async def update_region(self, region_id: str, update_data: ShippingTemplateRegionUpdate) -> ShippingTemplateRegion:
        """更新运费模板区域配置"""
        region = await self.get_region(region_id)

        # 验证区域格式
        if update_data.region_codes is not None and not update_data.region_codes.strip():
            raise ValidationException("区域代码不能为空")
        if update_data.region_names is not None and not update_data.region_names.strip():
            raise ValidationException("区域名称不能为空")

        # 更新字段
        update_dict = update_data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(region, k, v)

        await self.db.commit()
        await self.db.refresh(region)
        return region

    async def delete_region(self, region_id: str) -> None:
        """删除运费模板区域配置"""
        region = await self.get_region(region_id)

        await self.db.delete(region)
        await self.db.commit()

    async def get_template_with_regions(self, template_id: str) -> dict:
        """获取运费模板及其区域配置"""
        template = await self.get_template(template_id)

        result = await self.db.execute(
            select(ShippingTemplateRegion)
            .where(
                ShippingTemplateRegion.template_id == template_id,
                ShippingTemplateRegion.is_active == True
            )
            .order_by(ShippingTemplateRegion.created_at.asc())
        )
        regions = list(result.scalars().all())

        return {
            "template": template,
            "regions": regions
        }

    async def calculate_shipping_cost(
        self,
        template_id: str,
        region_code: Optional[str] = None,
        weight: Optional[int] = None,
        quantity: Optional[int] = None,
        volume: Optional[int] = None,
        total_amount: Optional[int] = None
    ) -> dict:
        """
        计算运费

        Args:
            template_id: 运费模板ID
            region_code: 区域代码
            weight: 重量(克)
            quantity: 数量
            volume: 体积(cm3)
            total_amount: 订单总金额(分)

        Returns:
            dict: 包含运费、是否包邮、是否可配送等信息
        """
        template = await self.get_template(template_id)

        # 1. 检查模板级别的不配送区域
        excluded_regions = template.excluded_regions or []
        excluded_codes = [r.get('code') for r in excluded_regions if isinstance(r, dict)]
        if region_code and region_code in excluded_codes:
            # 查找该区域的名称
            region_name = region_code
            for r in excluded_regions:
                if isinstance(r, dict) and r.get('code') == region_code:
                    region_name = r.get('name', region_code)
                    break
            return {
                "deliverable": False,
                "reason": "该地区不支持配送",
                "shipping_cost": 0,
                "free_shipping": False,
                "region_name": region_name,
                "region_code": region_code
            }

        # 2. 查找匹配的区域配置
        region = None
        if region_code:
            result = await self.db.execute(
                select(ShippingTemplateRegion)
                .where(
                    ShippingTemplateRegion.template_id == template_id,
                    ShippingTemplateRegion.is_active == True
                )
                .where(ShippingTemplateRegion.region_codes.like(f"%{region_code}%"))
            )
            region = result.scalar_one_or_none()

        # 3. 检查区域级别的不配送标志
        if region and region.is_excluded:
            return {
                "deliverable": False,
                "reason": "该地区不支持配送",
                "shipping_cost": 0,
                "free_shipping": False,
                "region_name": region.region_names,
                "region_code": region_code
            }

        # 4. 检查卖家承担运费（全场包邮）
        if template.free_shipping_type == "seller":
            return {
                "deliverable": True,
                "shipping_cost": 0,
                "free_shipping": True,
                "free_shipping_reason": "seller",
                "region_name": region.region_names if region else "默认区域",
                "region_code": region_code,
                "estimate_days_min": template.estimate_days_min,
                "estimate_days_max": template.estimate_days_max
            }

        # 5. 检查满件数包邮
        free_qty = None
        if region and region.free_quantity is not None:
            free_qty = region.free_quantity
        elif template.free_quantity is not None:
            free_qty = template.free_quantity

        if template.free_shipping_type == "quantity" and quantity and free_qty:
            if quantity >= free_qty:
                return {
                    "deliverable": True,
                    "shipping_cost": 0,
                    "free_shipping": True,
                    "free_shipping_reason": "quantity",
                    "region_name": region.region_names if region else "默认区域",
                    "region_code": region_code,
                    "estimate_days_min": template.estimate_days_min,
                    "estimate_days_max": template.estimate_days_max
                }

        # 6. 检查满金额包邮
        free_threshold = region.free_threshold if region and region.free_threshold is not None else template.free_threshold
        if free_threshold and total_amount and total_amount >= free_threshold:
            return {
                "deliverable": True,
                "shipping_cost": 0,
                "free_shipping": True,
                "free_shipping_reason": "amount",
                "region_name": region.region_names if region else "默认区域",
                "region_code": region_code,
                "estimate_days_min": template.estimate_days_min,
                "estimate_days_max": template.estimate_days_max
            }

        # 7. 使用区域配置或默认配置
        if not region:
            first_unit = template.default_first_unit
            first_cost = template.default_first_cost
            continue_unit = template.default_continue_unit
            continue_cost = template.default_continue_cost
        else:
            first_unit = region.first_unit
            first_cost = region.first_cost
            continue_unit = region.continue_unit
            continue_cost = region.continue_cost

        # 8. 根据计费方式计算运费
        shipping_cost = 0
        charge_type = template.charge_type

        if charge_type == "weight" and weight:
            # 按重量计费
            if weight <= first_unit:
                shipping_cost = first_cost
            else:
                extra_units = (weight - first_unit) // continue_unit
                if (weight - first_unit) % continue_unit > 0:
                    extra_units += 1
                shipping_cost = first_cost + extra_units * continue_cost
        elif charge_type == "quantity" and quantity:
            # 按件数计费
            if quantity <= first_unit:
                shipping_cost = first_cost
            else:
                extra_units = (quantity - first_unit) // continue_unit
                if (quantity - first_unit) % continue_unit > 0:
                    extra_units += 1
                shipping_cost = first_cost + extra_units * continue_cost
        elif charge_type == "volume" and volume:
            # 按体积计费
            volume_unit = template.volume_unit or 1  # 默认体积单位为1cm3
            if volume <= first_unit * volume_unit:
                shipping_cost = first_cost
            else:
                # 按体积单位计算续费
                extra_volume = volume - first_unit * volume_unit
                extra_units = extra_volume // (continue_unit * volume_unit)
                if extra_volume % (continue_unit * volume_unit) > 0:
                    extra_units += 1
                shipping_cost = first_cost + extra_units * continue_cost
        elif charge_type == "fixed":
            # 固定运费
            shipping_cost = first_cost

        return {
            "deliverable": True,
            "shipping_cost": shipping_cost,
            "free_shipping": False,
            "region_name": region.region_names if region else "默认区域",
            "region_code": region_code,
            "charge_type": charge_type,
            "first_unit": first_unit,
            "first_cost": first_cost,
            "continue_unit": continue_unit,
            "continue_cost": continue_cost,
            "estimate_days_min": template.estimate_days_min,
            "estimate_days_max": template.estimate_days_max
        }
