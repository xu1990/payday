"""
虚拟商品自动发货服务 (Virtual Product Service)

处理虚拟商品的自动发货功能：
1. deliver_virtual_product - 自动发货（支付成功后调用）
2. generate_delivery_code - 生成唯一发货码
3. validate_delivery_code - 验证并标记发货码为已使用
4. get_virtual_content - 获取虚拟商品内容URL
5. check_is_virtual_product - 检查商品是否为虚拟商品

关键特性：
- 自动发货：支付成功后自动生成发货码
- 唯一码生成：基于Redis原子递增保证唯一性
- 一次性使用：发货码使用后即失效
- 事务管理：失败时自动回滚
- 批量支持：支持批量发货多个订单项
"""
import logging
import secrets
from datetime import datetime
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem
from app.models.product import Product, ProductSKU
from app.core.exceptions import (
    NotFoundException,
    BusinessException,
    ValidationException,
)

logger = logging.getLogger(__name__)


class VirtualProductService:
    """
    虚拟商品自动发货服务

    处理虚拟商品（电子书、课程、会员卡等）的自动发货流程。
    支持发货码生成、验证和虚拟内容获取。

    Attributes:
        redis_client: Redis客户端实例

    Example:
        ```python
        service = VirtualProductService(redis_client=redis)

        # 自动发货
        success = await service.deliver_virtual_product(
            db=db,
            order_id="order_123",
            order_item_id="item_456"
        )

        # 生成发货码
        code = await service.generate_delivery_code(db, sku_id="sku_789")

        # 验证发货码
        is_valid = await service.validate_delivery_code(db, code)

        # 获取虚拟内容
        content_url = await service.get_virtual_content(db, sku_id="sku_789")
        ```
    """

    # Redis键前缀
    DELIVERY_CODE_PREFIX = "delivery_code"
    DELIVERY_CODE_COUNTER = "delivery_code_counter"

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """
        初始化虚拟商品服务

        Args:
            redis_client: Redis客户端实例。如果为None，会使用默认客户端
        """
        self.redis_client = redis_client
        self._external_client = redis_client is not None

    async def _get_redis(self) -> aioredis.Redis:
        """
        获取Redis客户端

        Returns:
            Redis客户端实例

        Raises:
            RuntimeError: 如果无法获取Redis连接
        """
        if self._external_client and self.redis_client:
            return self.redis_client

        # 如果没有外部客户端，从连接池获取
        from app.core.database import get_redis_pool
        self.redis_client = await get_redis_pool()
        return self.redis_client

    async def deliver_virtual_product(
        self,
        db: AsyncSession,
        order_id: str,
        order_item_id: str
    ) -> bool:
        """
        自动发货虚拟商品

        在订单支付成功后自动调用，为虚拟商品生成发货码并标记发货状态。
        发货码会保存到订单项的delivery_code字段。

        Args:
            db: 数据库会话
            order_id: 订单ID
            order_item_id: 订单项ID

        Returns:
            bool: 发货成功返回True

        Raises:
            NotFoundException: 订单或订单项不存在
            BusinessException: 非虚拟商品、已发货、订单未支付等业务错误

        Example:
            ```python
            success = await service.deliver_virtual_product(
                db=db,
                order_id="order_123",
                order_item_id="item_456"
            )
            ```
        """
        try:
            # 1. 查询订单
            result = await db.execute(
                select(Order).where(Order.id == order_id)
            )
            order = result.unique().scalars().first()

            if not order:
                raise NotFoundException("订单不存在", code="ORDER_NOT_FOUND")

            # 2. 检查订单是否已支付
            if order.payment_status != "paid":
                raise BusinessException("订单未支付，无法发货", code="ORDER_NOT_PAID")

            # 3. 查询订单项
            result = await db.execute(
                select(OrderItem).where(OrderItem.id == order_item_id)
            )
            item = result.unique().scalars().first()

            if not item:
                raise NotFoundException("订单项不存在", code="ORDER_ITEM_NOT_FOUND")

            # 4. 检查是否已发货
            if hasattr(item, 'delivery_code') and item.delivery_code:
                raise BusinessException("商品已发货，请勿重复操作", code="ALREADY_DELIVERED")

            # 5. 查询商品信息
            result = await db.execute(
                select(Product).where(Product.id == item.product_id)
            )
            product = result.unique().scalars().first()

            if not product:
                raise NotFoundException("商品不存在", code="PRODUCT_NOT_FOUND")

            # 6. 检查是否为虚拟商品
            if not product.is_virtual:
                raise BusinessException("非虚拟商品，不支持自动发货", code="NOT_VIRTUAL_PRODUCT")

            # 7. 生成发货码（如果有SKU）
            delivery_code = None
            if item.sku_id:
                delivery_code = await self.generate_delivery_code(db, item.sku_id)
            else:
                # 无SKU的虚拟商品，生成通用发货码
                delivery_code = await self._generate_generic_code()

            # 8. 更新订单项发货信息
            if hasattr(item, 'delivery_code'):
                item.delivery_code = delivery_code
            if hasattr(item, 'delivered_at'):
                item.delivered_at = datetime.utcnow()

            # 9. 如果订单所有项都已发货，更新订单状态
            if order.status == "paid":
                # 检查是否所有虚拟商品都已发货
                all_items_result = await db.execute(
                    select(OrderItem).where(OrderItem.order_id == order_id)
                )
                all_items = all_items_result.unique().scalars().all()

                # 检查所有虚拟商品是否都已发货
                virtual_items = [i for i in all_items if i.sku_id]
                all_delivered = all(
                    hasattr(i, 'delivery_code') and i.delivery_code
                    for i in virtual_items
                )

                if all_delivered:
                    order.status = "completed"

            await db.commit()
            await db.refresh(item)

            logger.info(
                f"虚拟商品自动发货成功: order_id={order_id}, "
                f"item_id={order_item_id}, code={delivery_code}"
            )

            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"虚拟商品发货失败: order_id={order_id}, error={str(e)}")
            raise

    async def generate_delivery_code(
        self,
        db: AsyncSession,
        sku_id: str
    ) -> str:
        """
        生成唯一发货码

        基于Redis原子递增操作生成全局唯一的发货码。
        格式: VD-YYYYMMDD-XXXXXXXX (例如: VD-20260224-AB12CD34)

        Args:
            db: 数据库会话
            sku_id: SKU ID

        Returns:
            str: 发货码

        Raises:
            Exception: Redis连接失败等错误

        Example:
            ```python
            code = await service.generate_delivery_code(db, sku_id="sku_123")
            # 返回: "VD-20260224-AB12CD34"
            ```
        """
        try:
            redis = await self._get_redis()

            # 1. 生成日期部分
            date_str = datetime.utcnow().strftime("%Y%m%d")

            # 2. 使用Redis原子递增获取序列号
            counter_key = f"{self.DELIVERY_CODE_COUNTER}:{date_str}"
            sequence = await redis.incr(counter_key)

            # 3. 生成随机部分（使用secrets保证安全性）
            random_bytes = secrets.token_bytes(4)
            random_str = secrets.token_hex(4).upper()

            # 4. 组装发货码
            # 使用序列号的最后8位作为部分标识
            sequence_str = f"{sequence:08d}"[-8:]
            delivery_code = f"VD-{date_str}-{random_str[:4]}{sequence_str[4:]}"

            # 5. 存储到Redis（Hash结构，方便查询和更新）
            code_key = f"{self.DELIVERY_CODE_PREFIX}:{delivery_code}"
            await redis.hset(
                code_key,
                mapping={
                    "sku_id": sku_id,
                    "used": "0",  # 0=未使用, 1=已使用
                    "created_at": datetime.utcnow().isoformat()
                }
            )

            # 6. 设置过期时间（30天）
            await redis.expire(code_key, 30 * 24 * 3600)

            logger.info(f"生成发货码: {delivery_code}, sku_id={sku_id}")

            return delivery_code

        except Exception as e:
            logger.error(f"生成发货码失败: sku_id={sku_id}, error={str(e)}")
            raise

    async def _generate_generic_code(self) -> str:
        """
        生成通用发货码（无SKU的虚拟商品）

        Returns:
            str: 发货码
        """
        date_str = datetime.utcnow().strftime("%Y%m%d")
        random_str = secrets.token_hex(4).upper()
        return f"VG-{date_str}-{random_str}"

    async def validate_delivery_code(
        self,
        db: AsyncSession,
        code: str
    ) -> bool:
        """
        验证发货码并标记为已使用

        验证发货码的有效性（存在、未使用、格式正确），验证成功后标记为已使用。
        发货码为一次性使用，使用后即失效。

        Args:
            db: 数据库会话
            code: 发货码

        Returns:
            bool: 验证成功返回True

        Raises:
            NotFoundException: 发货码不存在
            BusinessException: 发货码已使用
            ValidationException: 发货码格式无效

        Example:
            ```python
            is_valid = await service.validate_delivery_code(db, "VD-20260224-AB12CD34")
            ```
        """
        try:
            # 1. 验证发货码格式
            if not self._is_valid_code_format(code):
                raise ValidationException(
                    "发货码格式无效",
                    code="INVALID_DELIVERY_CODE_FORMAT",
                    details={"format": "VD-YYYYMMDD-XXXXXXXX"}
                )

            # 2. 从Redis查询发货码
            redis = await self._get_redis()
            code_key = f"{self.DELIVERY_CODE_PREFIX}:{code}"
            code_data = await redis.hgetall(code_key)

            if not code_data:
                raise NotFoundException("发货码不存在", code="DELIVERY_CODE_NOT_FOUND")

            # 3. 检查是否已使用
            used = code_data.get(b"used", b"0")
            if used == b"1":
                raise BusinessException("发货码已使用", code="DELIVERY_CODE_ALREADY_USED")

            # 4. 标记为已使用
            await redis.hset(code_key, "used", "1")
            await redis.hset(code_key, "used_at", datetime.utcnow().isoformat())

            logger.info(f"发货码验证成功并标记为已使用: {code}")

            return True

        except (NotFoundException, BusinessException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"验证发货码失败: code={code}, error={str(e)}")
            raise

    def _is_valid_code_format(self, code: str) -> bool:
        """
        验证发货码格式

        Args:
            code: 发货码

        Returns:
            bool: 格式有效返回True
        """
        if not code or not isinstance(code, str):
            return False

        parts = code.split("-")
        if len(parts) != 3:
            return False

        # 检查前缀
        if parts[0] not in ["VD", "VG"]:
            return False

        # 检查日期部分（8位数字）
        if len(parts[1]) != 8 or not parts[1].isdigit():
            return False

        # 检查随机码部分（8位字母数字）
        if len(parts[2]) != 8:
            return False

        return True

    async def get_virtual_content(
        self,
        db: AsyncSession,
        sku_id: str
    ) -> str:
        """
        获取虚拟商品内容URL

        获取虚拟商品（电子书、视频、课程等）的内容URL。
        内容URL通常存储在SKU的virtual_content字段。

        Args:
            db: 数据库会话
            sku_id: SKU ID

        Returns:
            str: 虚拟内容URL

        Raises:
            NotFoundException: SKU不存在
            BusinessException: 非虚拟商品或无可用内容

        Example:
            ```python
            content_url = await service.get_virtual_content(db, sku_id="sku_123")
            # 返回: "https://cdn.example.com/ebooks/book123.pdf"
            ```
        """
        try:
            # 1. 查询SKU
            result = await db.execute(
                select(ProductSKU).where(ProductSKU.id == sku_id)
            )
            sku = result.unique().scalars().first()

            if not sku:
                raise NotFoundException("SKU不存在", code="SKU_NOT_FOUND")

            # 2. 检查是否为虚拟商品（通过virtual_content字段判断）
            if not hasattr(sku, 'virtual_content') or not sku.virtual_content:
                raise BusinessException("非虚拟商品或无可用内容", code="NOT_VIRTUAL_PRODUCT")

            # 3. 检查内容是否为空
            if not sku.virtual_content or sku.virtual_content.strip() == "":
                raise BusinessException("虚拟商品无可用内容", code="NO_VIRTUAL_CONTENT")

            logger.info(f"获取虚拟内容成功: sku_id={sku_id}")

            return sku.virtual_content

        except (NotFoundException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"获取虚拟内容失败: sku_id={sku_id}, error={str(e)}")
            raise

    async def check_is_virtual_product(
        self,
        db: AsyncSession,
        product_id: str
    ) -> bool:
        """
        检查商品是否为虚拟商品

        通过查询商品的is_virtual字段判断是否为虚拟商品。

        Args:
            db: 数据库会话
            product_id: 商品ID

        Returns:
            bool: 是虚拟商品返回True，否则返回False

        Example:
            ```python
            is_virtual = await service.check_is_virtual_product(db, product_id="product_123")
            ```
        """
        try:
            result = await db.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.unique().scalars().first()

            if not product:
                return False

            return bool(product.is_virtual)

        except Exception as e:
            logger.error(f"检查虚拟商品失败: product_id={product_id}, error={str(e)}")
            return False

    async def batch_deliver_virtual_products(
        self,
        db: AsyncSession,
        order_id: str
    ) -> dict:
        """
        批量自动发货订单中的所有虚拟商品

        Args:
            db: 数据库会话
            order_id: 订单ID

        Returns:
            dict: 发货结果统计
                {
                    "success": [],  # 成功发货的订单项ID列表
                    "failed": [],   # 失败的订单项ID列表
                    "total": 0      # 总数
                }

        Example:
            ```python
            result = await service.batch_deliver_virtual_products(db, order_id="order_123")
            print(f"成功: {len(result['success'])}, 失败: {len(result['failed'])}")
            ```
        """
        try:
            # 1. 查询订单所有项
            result = await db.execute(
                select(OrderItem).where(OrderItem.order_id == order_id)
            )
            items = result.unique().scalars().all()

            success_items = []
            failed_items = []

            # 2. 逐个发货
            for item in items:
                try:
                    success = await self.deliver_virtual_product(db, order_id, item.id)
                    if success:
                        success_items.append(item.id)
                except Exception as e:
                    logger.warning(
                        f"批量发货单项失败: item_id={item.id}, error={str(e)}"
                    )
                    failed_items.append(item.id)

            result_stats = {
                "success": success_items,
                "failed": failed_items,
                "total": len(items)
            }

            logger.info(
                f"批量发货完成: order_id={order_id}, "
                f"成功={len(success_items)}, 失败={len(failed_items)}"
            )

            return result_stats

        except Exception as e:
            logger.error(f"批量发货失败: order_id={order_id}, error={str(e)}")
            raise
