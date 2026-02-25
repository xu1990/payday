"""
购物车服务 (Shopping Cart Service)

使用Redis实现购物车数据持久化，集成库存锁定服务：
1. get_cart - 获取用户购物车（含 totals 计算）
2. add_item - 添加商品到购物车（带库存锁定）
3. update_item - 更新购物车商品数量
4. remove_item - 移除购物车商品
5. clear_cart - 清空购物车

关键特性：
- Redis持久化：TTL 30分钟
- 库存锁定：添加/更新时锁定库存
- 自动计算：金额、积分、数量
- 错误处理：优雅降级

使用场景：
- 用户浏览商品时添加到购物车
- 用户在购物车调整数量
- 用户下单前确认购物车
- 订单完成后清空购物车
"""
import json
import logging
from typing import List, Optional
from uuid import uuid4

import redis.asyncio as aioredis
from app.core.exceptions import BusinessException, NotFoundException
from app.models.product import Product, ProductPrice, ProductSKU
from app.schemas.cart import CartItemResponse, CartResponse, ProductBasicInfo, SKUBasicInfo
from app.services.stock_lock import StockLockService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Redis key patterns
CART_KEY_PREFIX = "cart:user:"
CART_TTL = 1800  # 30 minutes


class CartService:
    """
    购物车服务

    使用Redis存储购物车数据，提供增删改查功能。

    Attributes:
        redis_client: Redis客户端实例
        CART_TTL: 购物车数据TTL（秒），默认1800秒（30分钟）

    Example:
        ```python
        service = CartService(redis_client=redis)

        # 添加商品到购物车
        cart = await service.add_item(
            db=db,
            user_id="user_123",
            sku_id="sku_123",
            quantity=2
        )

        # 获取购物车
        cart = await service.get_cart(user_id="user_123")

        # 更新数量
        cart = await service.update_item(
            user_id="user_123",
            item_id="item_123",
            quantity=5
        )

        # 移除商品
        cart = await service.remove_item(
            user_id="user_123",
            item_id="item_123"
        )

        # 清空购物车
        await service.clear_cart(user_id="user_123")
        ```
    """

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """
        初始化购物车服务

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

        # 使用默认Redis客户端
        from app.core.cache import get_redis_client
        try:
            return await get_redis_client()
        except Exception as e:
            logger.error(f"Failed to get Redis client: {e}")
            raise RuntimeError(f"Failed to get Redis client: {e}")

    def _get_cart_key(self, user_id: str) -> str:
        """
        获取购物车Redis键

        Args:
            user_id: 用户ID

        Returns:
            Redis键
        """
        return f"{CART_KEY_PREFIX}{user_id}"

    async def get_cart(self, user_id: str) -> CartResponse:
        """
        获取用户购物车

        从Redis读取购物车数据，计算totals，刷新TTL。

        Args:
            user_id: 用户ID

        Returns:
            CartResponse: 购物车响应对象

        Raises:
            RuntimeError: Redis连接失败
        """
        try:
            redis = await self._get_redis()
            cart_key = self._get_cart_key(user_id)

            # 获取所有购物车项
            cart_items_data = await redis.hgetall(cart_key)

            # 解析并构建购物车项列表
            items = []
            total_amount = 0
            total_points = 0
            item_count = 0

            for item_json in cart_items_data.values():
                try:
                    item_data = json.loads(item_json)
                    item = CartItemResponse(**item_data)
                    items.append(item)

                    # 计算totals
                    sku = item_data.get("sku", {})
                    quantity = item_data.get("quantity", 0)
                    price = sku.get("price", 0)
                    currency = sku.get("currency", "CNY")

                    if currency == "POINTS":
                        # 积分商品
                        total_points += int(price * quantity)
                    else:
                        # 现金商品（元转分）
                        total_amount += int(price * 100 * quantity)

                    item_count += quantity

                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse cart item: {e}")
                    # 跳过无效项
                    continue

            # 刷新TTL
            await redis.expire(cart_key, CART_TTL)

            return CartResponse(
                items=items,
                total_amount=total_amount,
                total_points=total_points,
                item_count=item_count
            )

        except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
            logger.error(f"Redis connection error getting cart for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting cart for user {user_id}: {e}")
            raise

    async def add_item(
        self,
        db: AsyncSession,
        user_id: str,
        sku_id: str,
        quantity: int
    ) -> CartResponse:
        """
        添加商品到购物车

        如果商品已存在，增加数量；否则添加新项。
        添加时会锁定库存。

        Args:
            db: 数据库session
            user_id: 用户ID
            sku_id: SKU ID
            quantity: 数量

        Returns:
            CartResponse: 更新后的购物车

        Raises:
            NotFoundException: SKU不存在
            BusinessException: 库存不足
        """
        # 参数验证
        if quantity < 1:
            raise BusinessException("数量必须大于等于1", code="INVALID_QUANTITY")

        try:
            redis = await self._get_redis()
            cart_key = self._get_cart_key(user_id)

            # 检查SKU是否已存在
            existing_item_json = await redis.hget(cart_key, sku_id)

            # 获取SKU和商品信息
            sku = await self._get_sku(db, sku_id)
            product = await self._get_product(db, sku.product_id)

            # 获取SKU价格
            price_info = await self._get_sku_price(db, sku_id)

            # 初始化库存锁定服务
            stock_lock_service = StockLockService(redis_client=redis)

            if existing_item_json:
                # 商品已存在，增加数量
                item_data = json.loads(existing_item_json)
                old_quantity = item_data["quantity"]
                new_quantity = old_quantity + quantity

                # 锁定新增的库存
                locked = await stock_lock_service.acquire_stock_lock(sku_id, quantity)
                if not locked:
                    raise BusinessException("库存不足", code="INSUFFICIENT_STOCK")

                # 更新数量
                item_data["quantity"] = new_quantity
                item_json = json.dumps(item_data, ensure_ascii=False)
                await redis.hset(cart_key, sku_id, item_json)

            else:
                # 新商品，锁定全部库存
                locked = await stock_lock_service.acquire_stock_lock(sku_id, quantity)
                if not locked:
                    raise BusinessException("库存不足", code="INSUFFICIENT_STOCK")

                # 构建购物车项
                item_data = {
                    "id": str(uuid4()),
                    "sku_id": sku_id,
                    "quantity": quantity,
                    "product": {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "images": product.images,
                        "product_type": product.product_type,
                        "item_type": product.item_type,
                        "is_active": product.is_active
                    },
                    "sku": {
                        "id": sku.id,
                        "sku_code": sku.sku_code,
                        "name": sku.name,
                        "attributes": sku.attributes,
                        "stock": sku.stock,
                        "price": price_info["price"],
                        "currency": price_info["currency"]
                    }
                }
                item_json = json.dumps(item_data, ensure_ascii=False)
                await redis.hset(cart_key, sku_id, item_json)

            # 设置TTL
            await redis.expire(cart_key, CART_TTL)

            # 返回更新后的购物车
            return await self.get_cart(user_id)

        except (NotFoundException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"Error adding item to cart for user {user_id}: {e}")
            raise

    async def update_item(
        self,
        user_id: str,
        item_id: str,
        quantity: int
    ) -> CartResponse:
        """
        更新购物车商品数量

        根据数量变化锁定或释放库存。

        Args:
            user_id: 用户ID
            item_id: 购物车项ID
            quantity: 新数量

        Returns:
            CartResponse: 更新后的购物车

        Raises:
            NotFoundException: 购物车项不存在
            BusinessException: 库存不足
        """
        # 参数验证
        if quantity < 1:
            raise BusinessException("数量必须大于等于1", code="INVALID_QUANTITY")

        try:
            redis = await self._get_redis()
            cart_key = self._get_cart_key(user_id)

            # 获取所有购物车项
            cart_items_data = await redis.hgetall(cart_key)

            # 查找目标项
            target_item = None
            target_sku_id = None

            for sku_id, item_json in cart_items_data.items():
                item_data = json.loads(item_json)
                if item_data.get("id") == item_id:
                    target_item = item_data
                    target_sku_id = sku_id
                    break

            if not target_item:
                raise NotFoundException("购物车项不存在")

            # 计算数量变化
            old_quantity = target_item["quantity"]
            quantity_diff = quantity - old_quantity

            # 初始化库存锁定服务
            stock_lock_service = StockLockService(redis_client=redis)

            if quantity_diff > 0:
                # 增加数量，锁定库存
                locked = await stock_lock_service.acquire_stock_lock(
                    target_sku_id,
                    quantity_diff
                )
                if not locked:
                    raise BusinessException("库存不足", code="INSUFFICIENT_STOCK")
            elif quantity_diff < 0:
                # 减少数量，释放库存
                await stock_lock_service.release_stock_lock(
                    target_sku_id,
                    abs(quantity_diff)
                )

            # 更新数量
            target_item["quantity"] = quantity
            item_json = json.dumps(target_item, ensure_ascii=False)
            await redis.hset(cart_key, target_sku_id, item_json)

            # 设置TTL
            await redis.expire(cart_key, CART_TTL)

            # 返回更新后的购物车
            return await self.get_cart(user_id)

        except (NotFoundException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"Error updating cart item for user {user_id}: {e}")
            raise

    async def remove_item(
        self,
        user_id: str,
        item_id: str
    ) -> CartResponse:
        """
        移除购物车商品

        释放该商品的所有库存锁定。

        Args:
            user_id: 用户ID
            item_id: 购物车项ID

        Returns:
            CartResponse: 更新后的购物车

        Raises:
            NotFoundException: 购物车项不存在
        """
        try:
            redis = await self._get_redis()
            cart_key = self._get_cart_key(user_id)

            # 获取所有购物车项
            cart_items_data = await redis.hgetall(cart_key)

            # 查找目标项
            target_item = None
            target_sku_id = None

            for sku_id, item_json in cart_items_data.items():
                item_data = json.loads(item_json)
                if item_data.get("id") == item_id:
                    target_item = item_data
                    target_sku_id = sku_id
                    break

            if not target_item:
                raise NotFoundException("购物车项不存在")

            # 释放库存锁定
            quantity = target_item["quantity"]
            stock_lock_service = StockLockService(redis_client=redis)
            await stock_lock_service.release_stock_lock(target_sku_id, quantity)

            # 删除购物车项
            await redis.hdel(cart_key, target_sku_id)

            # 设置TTL
            await redis.expire(cart_key, CART_TTL)

            # 返回更新后的购物车
            return await self.get_cart(user_id)

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error removing cart item for user {user_id}: {e}")
            raise

    async def clear_cart(self, user_id: str) -> None:
        """
        清空购物车

        释放所有商品的库存锁定。

        Args:
            user_id: 用户ID
        """
        try:
            redis = await self._get_redis()
            cart_key = self._get_cart_key(user_id)

            # 获取所有购物车项
            cart_items_data = await redis.hgetall(cart_key)

            # 释放所有库存锁定
            stock_lock_service = StockLockService(redis_client=redis)

            for sku_id, item_json in cart_items_data.items():
                try:
                    item_data = json.loads(item_json)
                    quantity = item_data.get("quantity", 0)
                    await stock_lock_service.release_stock_lock(sku_id, quantity)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse cart item for stock release: {e}")
                    continue

            # 删除整个购物车
            await redis.delete(cart_key)

        except Exception as e:
            logger.error(f"Error clearing cart for user {user_id}: {e}")
            raise

    async def _get_sku(self, db: AsyncSession, sku_id: str) -> ProductSKU:
        """
        获取SKU信息

        Args:
            db: 数据库session
            sku_id: SKU ID

        Returns:
            ProductSKU: SKU对象

        Raises:
            NotFoundException: SKU不存在
        """
        result = await db.execute(
            select(ProductSKU).where(ProductSKU.id == sku_id)
        )
        sku = result.scalar_one_or_none()

        if not sku:
            raise NotFoundException("SKU不存在")

        if not sku.is_active:
            raise BusinessException("SKU已下架", code="SKU_INACTIVE")

        return sku

    async def _get_product(self, db: AsyncSession, product_id: str) -> Product:
        """
        获取商品信息

        Args:
            db: 数据库session
            product_id: 商品ID

        Returns:
            Product: 商品对象

        Raises:
            NotFoundException: 商品不存在
        """
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            raise NotFoundException("商品不存在")

        if not product.is_active:
            raise BusinessException("商品已下架", code="PRODUCT_INACTIVE")

        return product

    async def _get_sku_price(self, db: AsyncSession, sku_id: str) -> dict:
        """
        获取SKU价格

        优先获取基础价格（base type）。

        Args:
            db: 数据库session
            sku_id: SKU ID

        Returns:
            dict: 包含price和currency的字典

        Raises:
            NotFoundException: 价格不存在
        """
        result = await db.execute(
            select(ProductPrice)
            .where(ProductPrice.sku_id == sku_id)
            .where(ProductPrice.price_type == "base")
            .where(ProductPrice.is_active == True)
            .order_by(ProductPrice.created_at.desc())
        )
        price = result.scalar_one_or_none()

        if not price:
            # 如果没有base price，尝试获取任何active price
            result = await db.execute(
                select(ProductPrice)
                .where(ProductPrice.sku_id == sku_id)
                .where(ProductPrice.is_active == True)
                .order_by(ProductPrice.created_at.desc())
            )
            price = result.scalar_one_or_none()

        if not price:
            raise NotFoundException("SKU价格不存在")

        return {
            "price": float(price.price_amount),
            "currency": price.currency
        }
